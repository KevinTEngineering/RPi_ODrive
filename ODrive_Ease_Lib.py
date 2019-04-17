import odrive
from odrive.enums import *
import time
import usb.core

# Used to make using the ODrive easier Version 2.0.1
# Last update April 17, 2019 by Blake Lazarine

def find_ODrives():
    dev = usb.core.find(find_all=1, idVendor=0x1209, idProduct=0x0d32)
    od = []
    try:
        while True:
            a = next(dev)
            od.append(odrive.find_any('usb:%s:%s' % (a.bus, a.address)))
            print('added')
    except:
        pass
    return od

class ODrive_Axis(object):

    def __init__(self, axis, vel_lim=20000):
        self.axis = axis
        self.zero = 0;
        self.axis.controller.config.vel_limit = vel_lim

    def calibrate(self):
        self.axis.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
        start = time.time()
        while self.axis.current_state != AXIS_STATE_IDLE:
            time.sleep(0.1)
            if time.time() - start > 15:
                print("could not calibrate, try rebooting odrive")
                return False


    def is_calibrated(self):
        return self.axis.motor.is_calibrated

    def set_vel(self, vel):
        self.axis.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
        self.axis.controller.config.control_mode = CTRL_MODE_VELOCITY_CONTROL
        self.axis.controller.vel_setpoint = vel

    def set_vel_limit(self, vel):
        self.axis.controller.config.vel_limit = vel

    def get_vel_limit(self):
        return self.axis.controller.config.vel_limit
    
    def set_zero(self, pos):
        self.zero = pos

    def get_pos(self):
        return self.axis.encoder.pos_estimate - self.zero

    def get_raw_pos(self):
        return self.axis.encoder.pos_estimate

    def set_pos(self, pos):
        desired_pos = pos + self.zero
        self.axis.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
        self.axis.controller.config.control_mode = CTRL_MODE_POSITION_CONTROL
        self.axis.controller.pos_setpoint = desired_pos

    def set_pos_trap(self, pos):
        desired_pos = pos + self.zero
        self.axis.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
        self.axis.controller.config.control_mode = CTRL_MODE_TRAJECTORY_CONTROL
        self.axis.controller.move_to_pos(desired_pos)

    def set_curr_limit(self, val):
        self.axis.motor.config.current_lim = val

    def get_curr_limit(self):
        return self.axis.motor.config.current_lim
    
    def set_current(self, curr):
        self.axis.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
        self.axis.controller.config.control_mode = CTRL_MODE_CURRENT_CONTROL
        self.axis.controller.current_setpoint = curr

    def get_vel(self):
        return self.axis.encoder.vel_estimate

    def set_pos_gain(self, val):
        self.axis.controller.config.pos_gain = val

    def get_pos_gain(self):
        return self.axis.controller.config.pos_gain

    def set_vel_gain(self, val):
        self.axis.controller.config.vel_gain = val

    def get_vel_gain(self):
        return self.axis.controller.config.vel_gain

    def set_vel_integrator_gain(self, val):
        self.axis.controller.config.vel_integrator_gain = val

    def get_vel_integrator_gain(self):
        return self.axis.controller.config.vel_integrator_gain

    def is_busy(self, speed=500):
        if(abs(self.get_vel())) > speed:
            return True
        else:
            return False

    def set_calibration_current(self, curr):
        self.axis.motor.config.calibration_current = curr

    def get_calibration_current(self):
        return self.axis.motor.config.calibration_current

    # method to home ODrive using where the chassis is mechanically stopped
    # length is expected length of the track the ODrive takes
    # set length to -1 if you do not want the ODrive to check its homing
    # direction = 1 or -1 depending on which side of the track you want home to be at
    # use direction = 1 if you want the track to be of only positive location values
    def home(self, current1, current2, length=-1, direction=1):
        self.set_current(current1 * -1 * direction)
        print('here')
        time.sleep(1)
        print('there')
        while self.is_busy():
            pass

        time.sleep(1)

        self.set_zero(self.get_raw_pos())
        print(self.get_pos())

        time.sleep(1)

        if not length == -1:
            self.set_current(current2 * 1 * direction)
            time.sleep(1)
            while self.is_busy():
                pass

            # end pos should be length
            if abs(self.get_pos() - length) > 50:
                print('ODrive could not home correctly')
                # maybe throw a more formal error here
                return False

        self.set_pos(0)
        print('ODrive homed correctly')
        return True

    def home_with_vel(self, vel, length=-1, direction=1):
        self.set_vel(vel * -1 * direction)
        print('here')
        time.sleep(1)
        print('there')
        while self.is_busy():
            pass

        time.sleep(1)

        self.set_zero(self.get_raw_pos())
        print(self.get_pos())

        time.sleep(1)

        if not length == -1:
            self.set_vel(vel * 1 * direction)
            time.sleep(1)
            while self.is_busy():
                pass

            print(self.get_pos())

            # end pos should be length
            if abs(self.get_pos() - length) > 50:
                print('ODrive could not home correctly')
                # maybe throw a more formal error here
                return False

        print('ODrive homed correctly')
        return True

    #returns phase B current going into motor
    def get_curr_B(self):
        return self.axis.motor.current_meas_phB

    # returns phase C current going into motor
    def get_curr_C(self):
        return self.axis.motor.current_meas_phC


class double_ODrive(object):
    
    #ax_X and ax_Y are ODrive_Axis objects
    def __init__(self, ax_X, ax_Y):
        self.y = ax_X
        self.x = ax_Y

    def calibrate(self):
        self.x.axis.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
        self.y.axis.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
        start = time.time()
        while self.x.axis.current_state != AXIS_STATE_IDLE or self.x.axis.current_state != AXIS_STATE_IDLE:
            time.sleep(0.1)
            if time.time() - start > 15:
                print('could not calibrate, try rebooting odrive')
                return False

    def get_pos(self):
        return [x.get_pos, y.get_pos()]

    def set_pos(self, pos_x, pos_y):
        self.x.set_pos(pos_x)
        self.y.set_pos(pos_y)

    def home_with_vel(vel_x, vel_y):
        self.x.set_vel(vel_x)
        self.y.set_vel(vel_y)

        while(self.x.is_busy() or self.y.is_busy()):
            time.sleep(0.3)

        time.sleep(1)
        self.x.set_zero(x.get_raw_pos())
        self.y.set_zero(y.get_raw_pos())

        print("done homing")




print('ODrive Ease Lib 2.0.1')
'''
odrv0 = odrive.find_any()
print(str(odrv0.vbus_voltage))

ax = ODrive_Axis(odrv0.axis1)
ax.calibrate()
#ax.set_vel(10000)
#ax.home(0.05, -1)

'''
