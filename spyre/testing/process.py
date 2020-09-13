import thorlabs_apt as apt
import time

# display motors and assign them to Motor objects
elements = apt.list_available_devices()
serials = [x[1] for x in elements]
serial1 = serials[0]
serial2 = serials[1]
print('\n')
print("Present motor devices:", elements, '\n')
motor1 = apt.Motor(serial1)
motor2 = apt.Motor(serial2)

# home motors
print("Motor 1 homing parameters:", motor1.get_move_home_parameters())
print("Motor 2 homing parameters:", motor2.get_move_home_parameters())
motor1.move_home()
motor2.move_home()
print("Homing...\n")

while (not motor1.has_homing_been_completed or not motor2.has_homing_been_completed):
	continue

time.sleep(1)
input("Press any key to start readying")

# ready motors and then pull on user input
print("Motor 1 velocity parameters:", motor1.get_velocity_parameters())
print("Motor 2 velocity parameters:", motor2.get_velocity_parameters())
motor1.move_to(40)
motor2.move_to(40)
print("Readying...\n")

while (motor1.is_in_motion or motor2.is_in_motion):
	continue

time.sleep(1)
input("Press any key to start pulling")

# pull
print("Pulling...\n")
motor1.set_velocity_parameters(0, 0.01, 0.1) #(minimum_velocity, acceleration, maximum_velocity) in mm
motor2.set_velocity_parameters(0, 0.01, 0.1)
motor1.move_velocity(2)
motor1.move_to(20) # move to relative/absolute position
motor2.move_velocity(2)
motor2.move_to(20)

