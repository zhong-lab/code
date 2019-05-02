from PyQt5 import QtCore
import pandas as pd

class Node(QtCore.QObject):
    def __init__(self, name, dataframe=None, parent=None, metadata=None, delayed_params=None):
        if type(name)!=str or len(name)==0 or '/' in name: 
            raise NamingException("Name must be a non-empty string with no '/' character")
        super().__init__(parent=parent)
        self.children = dict()
        self.name = name
        self.dataframe = dataframe
        self.metadata = metadata
        self.delayed_params = delayed_params

    def set_data(self, dataframe):
        self.dataframe = dataframe

    def append_data(self, dataframe, **kwargs):
        self.dataframe = self.dataframe.append(dataframe, **kwargs)

    def get_data(self, keep_alive=True):
        if self.dataframe is None and not self.delayed_params is None:
            file_path, node_path = self.delayed_params
            with pd.HDFStore(file_path, mode='r') as store:
                df = store.get(node_path)
            if keep_alive:
                self.dataframe = df
            return df
        else:
            return self.dataframe

    def has_data(self):
        return not self.dataframe is None

    def add_node(self, name=None, node=None, overwrite=False, **kwargs):
        if name is None and node is None: 
            raise Exception('Must specify either <name> or <node>')
        if not name is None and not node is None: 
            raise Exception("Can't specify both <name> and <node>")
        if node is None: node = Node(name, parent=self, **kwargs)
        if type(node) != Node: 
            raise TypeError
        if self.has_child(node.name) and not overwrite: 
            raise NodeExistsException
        self.children[node.name] = node
        return node

    def has_child(self, name):
        return name in self.children.keys()

    def get_child(self, name):
        if name in self.children:
            return self.children[name]
        else: 
            raise NodeNotFoundException

    def add_meta(self, **kwargs):
        if self.metadata is None:
            self.metadata = kwargs
        else:
            self.metadata.update(kwargs)

    def get_meta(self, keep_alive=True):
        if self.metadata is None and not self.delayed_params is None:
            file_path, node_path = self.delayed_params
            with pd.HDFStore(file_path, mode='r') as store:
                meta = store.get_storer(node_path).attrs.metadata
            if keep_alive:
                self.metadata = meta
        else:
            meta = self.metadata
        if meta is None:
            return {}
        else:
            return meta

    def get_tree_str(self, prefix = '', previous_string=''):
        s = previous_string + prefix + '+ ' + self.name +'\n'
        prefix += '   '
        for name in self.get_child_names():
            s += self.children[name].get_tree_str(prefix=prefix)
        return s

    def get_child_names(self, sort=True):
        child_names = self.children.keys()
        if sort:
            return sorted(child_names, key=str.lower)
        else:
            return child_names


    def __str__(self):
        return self.get_tree_str()

    def __iter__(self):
        for name in self.children:
            yield self.children[name]


class Repository(QtCore.QObject):
    _VERSION = '1.0'

    def __init__(self, file_path, parent=None, delayed=True):
        super().__init__(parent=parent)
        self.root = Node('root')
        self.root.set_data(pd.DataFrame())
        self.root.add_meta(repository_version=self._VERSION)
        self.file_path = file_path
        self.load(delayed=delayed)
        return

    def load(self, delayed=True):
        try:
            with pd.HDFStore(self.file_path, mode='r') as store:
                nodes_list = store.keys()
                try:
                    nodes_list.pop(nodes_list.index('/__root'))
                    self.root.set_data(store.get('/__root'))
                    meta = store.get_storer('/__root').attrs.metadata
                    self.root.add_meta(**meta)
                except:
                    print('Could not load data_index')
                try:
                    version = self.root.get_meta()['repository_version']
                    if version != self._VERSION:
                        raise Exception
                except:
                    print('File repository version does not match the current verison of the code... You may have to open manually')
                nodes_list.sort(key=len)
                for path in nodes_list:
                    if delayed:
                        self.add_node(path=path, overwrite=True, delayed_params=[self.file_path, path])
                    else:
                        df = store.get(path)
                        try:
                            meta = store.get_storer(path).attrs.metadata
                        except:
                            meta = dict()
                        self.add_node(path=path, dataframe=df, metadata=meta, overwrite=True)
        except OSError:
            print("File does not exist")
            pass

    def save(self, overwrite=False):
        with pd.HDFStore(self.file_path, mode='a') as store:
            store_keys = store.keys()
            def save_node(_node, _prefix):
                path = _prefix + _node.name
                if not path in store_keys or overwrite:
                    if _node.has_data():
                        store.put(path, _node.get_data())
                        store.get_storer(path).attrs.metadata = _node.get_meta()
                for child in _node:
                    save_node(child, path+'/')
            #Save the root and then all the other nodes
            store.put('/__root', self.root.get_data())
            store.get_storer('/__root').attrs.metadata = self.root.get_meta()
            for top_node in self.root:
                save_node(top_node, '/')

    def get_node(self, path):
        if path[0] != '/': 
            path = '/' + path
        if path =='/' or path=='root':
            return self.root
        node = self.root
        for name in path.split('/')[1:]:
            node = node.get_child(name)
        return node

    def add_node(self, path=None, node=None, **kwargs):
        # Overloading the function with two ways of adding a node
        if node is None and path is None: 
            raise Exception('Must specify either <path> or <node>')
        if not path is None and not node is None: 
            raise Exception("Can't specify both <path> and <node>")

        if not node is None:
            return self.root.add_node(node=node, **kwargs)
        if not path is None:
            node = self.root
            for name in path.split('/')[1:-1]:
                if not node.has_child(name):
                    node.add_node(name=name)
                node = node.get_child(name)
            return node.add_node(name=path.split('/')[-1], **kwargs)

    def __str__(self):
        s = 'File Path: {}\n'.format('None' if self.file_path is None else self.file_path)
        s += self.root.__str__()
        return s

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, path):
        return self.get_node(path)

    def get_uid(self, force_reload=True):
        if force_reload:
            self.load(delayed=True)
        used_uid = [int(name[3:]) for name in self.root.get_child_names(sort=False)]
        if len(used_uid)==0:
            new_uid = 0
        else:
            new_uid = max(used_uid) + 1
        return int(new_uid)

    def add_entry(self, node, **kwargs):
        """
        This will add an entry to the index.  Note that the node name should be a uid.  
        Use get_uid to obtain a uid
        """
        index_entry = {k:[kwargs[k]] for k in kwargs}
        index_entry['uid']= [node.name]
        n = self.add_node(node=node)
        self.root.append_data(pd.DataFrame(index_entry), ignore_index=True)
        return n

    def get_index(self, col_order=[]):
        df = self.root.get_data()
        if len(col_order) == 0:
            return df
        else:
            for col in df.columns:
                if not col in col_order:
                    col_order.append(col)
            return df.reindex_axis(col_order, axis=1)




class NodeExistsException(Exception):
    pass

class NodeNotFoundException(Exception):
    pass

class NamingException(Exception):
    pass
