import RPi.GPIO as GPIO
from time import sleep
import dbus
from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor
import requests
import max30102
import hrcalc

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
m = max30102.MAX30102()
def get_approximate_location():
    try:
        response = requests.get('https://ipinfo.io')
        data = response.json()
        
        if 'loc' in data:
            latitude, longitude = map(float, data['loc'].split(','))
            return latitude, longitude
        else:
            print("Unable to get location data from the response.")
            return None, None

    except Exception as e:
        print("An error occurred:", e)
        return None, None

class WorksAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("SecurePi")
        self.include_tx_power = True

class WorksService(Service):
    WORKS_SERVICE_UUID = "00000001-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, index):
        Service.__init__(self, index, self.WORKS_SERVICE_UUID, True)
        self.add_characteristic(WorksCharacteristic(self))
        self.add_characteristic(GPSCharacteristic(self))

class GPSCharacteristic(Characteristic):
    WORKS_CHARACTERISTIC_UUID = "00000003-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service):
        Characteristic.__init__(
                self, self.WORKS_CHARACTERISTIC_UUID,
                ["read"], service)
        self.add_descriptor(GPSDescriptor(self))

    def ReadValue(self, options):
        latitude, longitude = get_approximate_location()
        value = [dbus.Byte(ord(str(latitude[i]))) for i in range(len(str(latitude)))]
        value.append(dbus.Byte(ord(',')))
        value.extend([dbus.Byte(ord(str(longitude[i]))) for i in range(len(str(longitude)))])
        return value

class GPSDescriptor(Descriptor):
    WORKS_DESCRIPTOR_UUID = "2901"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.WORKS_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        latitude, longitude = get_approximate_location()
        
        y=[0,0]
        timer=0
        while timer>7:
            red, ir = m.read_sequential()
            x=(hrcalc.calc_hr_and_spo2(ir,red))
            y[0]=x[0]
            y[1]=x[2]
            timer+=1
            
        desc = f"The latitude is {latitude} and longitude is {longitude}, Heartrate is: {y[0]}, SO2 lvl is: {y[1]}"
        value = [dbus.Byte(ord(desc[i])) for i in range(len(desc))]
        return value

class WorksCharacteristic(Characteristic):
    WORKS_CHARACTERISTIC_UUID = "00000002-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service):
        Characteristic.__init__(
                self, self.WORKS_CHARACTERISTIC_UUID,
                ["read"], service)
        self.add_descriptor(WorksDescriptor(self))

    def ReadValue(self, options):
        value = []

        message = "SecurePi"
        for c in message:
            value.append(dbus.Byte(c.encode()))

        return value

class WorksDescriptor(Descriptor):
    WORKS_DESCRIPTOR_UUID = "2901"
    WORKS_DESCRIPTOR_VALUE = "Test Message: Works"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.WORKS_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.WORKS_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value

app = Application()
app.add_service(WorksService(0))
app.register()

adv = WorksAdvertisement(0)
adv.register()
    
GPIO.setmode(GPIO.BCM)

sleepTime = .1

buttonPin = 17

GPIO.setup(buttonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    while True:
        if GPIO.input(buttonPin) == 0:
            try:
                app.run()
            except KeyboardInterrupt:
                app.quit()
            sleep(0.5)

finally:
    GPIO.cleanup()
