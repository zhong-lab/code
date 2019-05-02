import os
from pathlib import Path
import binascii

import yaml
from lantz import Q_

def represent_quantity(dumper, val):
    return dumper.represent_scalar(u'!Quantity', str(val))

def construct_quantity(loader, node):
    value = loader.construct_scalar(node)
    return Q_(value)

yaml.add_representer(Q_, represent_quantity)
yaml.add_constructor(u'!Quantity', construct_quantity)

class Persister(object):

    def __init__(self, base_dir=None, subpath_name='Spyre'):
        if base_dir is None:
            base_dir = os.getenv('APPDATA')
        base_path = Path(base_dir)
        subpath = base_path / subpath_name
        subpath.mkdir(exist_ok=True)
        self.subpath = subpath

        self.config_path = self.subpath / 'config.yml'
        if not self.config_path.exists():
            print('config file not found...creating...')
            self.config = {
                'instruments': dict(),
                'spyrelets': dict(),
            }
            self.dump()
        self.load()
        return

    def load(self):
        with self.config_path.open('r') as f:
            loaded = yaml.load(f)
        if loaded is None:
            self.config = {}
        else:
            self.config = loaded
        return

    def dump(self):
        with self.config_path.open('w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
        return

    def dump_spyrelets(self, dock_geom, spyrelets, spyrelets_elements):
        for sname, element_geometries in spyrelets.items():
            for element_name, element_geometry in element_geometries.items():
                element_geometries[element_name] = binascii.hexlify(element_geometry).decode('ascii')
            spyrelets[sname] = element_geometries
        self.config['spyrelets'] = {
            'spyrelet_dock_geometry': binascii.hexlify(dock_geom).decode('ascii'),
            'spyrelet_data': spyrelets,
        }
        self.config['spyrelets_elements'] = spyrelets_elements
        self.dump()
        return

    def load_spyrelets(self):
        self.load()
        dock_geom = binascii.unhexlify(self.config['spyrelets']['spyrelet_dock_geometry'].encode('ascii'))
        spyrelets = self.config['spyrelets']['spyrelet_data']
        spyrelets_elements = self.config['spyrelets_elements']
        for sname, element_geometries in spyrelets.items():
            for element_name, element_geometry in element_geometries.items():
                element_geometries[element_name] = binascii.unhexlify(element_geometry.encode('ascii'))
            spyrelets[sname] = element_geometries
        return dock_geom, spyrelets, spyrelets_elements

def test():
    p = Persister()

if __name__ == '__main__':
    test()
