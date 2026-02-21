"""
Futaba SBUS protocol parser module.

2026, Felix Althaus

Sources:
- https://github.com/Sokrates80/sbus_driver_micropython
- https://github.com/fifteenhex/python-sbus/tree/master
- https://github.com/bolderflight/sbus

SBUS is UART, 100'0000 8E2:
Speed:      100'0000 baud
Start Bit:  1
Data Bits:  8
Parity:     Even
Stop Bits:  1

Note that signals levels are inverted (idle level is logic low).
ON the OpenMV Cam h/ and H7+ with their STM32H743 processor, the UART RX input can be inverted
in software.


A SBUS message is 25 bytes long:

  ----------------------------------------------
  | 0x0F |Data 0|Data 1|...|Data N|Flags| 0x00 |
  ----------------------------------------------

There is no checksum.

"""


# TOOD: transfer to 'csi' and 'time' modules
from sys import platform
import sensor
from machine import UART, Pin
from pyb import micros, elapsed_micros
import stm


# TODO: Class name SBUS(), SBUSParser(), SBUSDecoder(), SBUSReceiver() ?

class SBUS:
    """
    Futaba SBUS Parser Class
    """

    CHANNELS = 16
    BITSIZE = 11
    OFFSET = 2**(BITSIZE-1)
    SCALING = 5
    CENTER = 1520



    def __init__(self, uart, invert=True):
        """
        Constructs a SBUS parser object, including setting up the UART:
        - 100'000 baud
        - 8E2
        - inverted signal levels wrt usual TTL convention

        Parameters:
            uart    Serial port (UART) to read data from
            invert  Invert RX input if True (default)

        Inputs can be inverted for OpenMV H7, H7+, pyboard does not support it.

        """
        # 100'000 baud 8E2
        # machine.UART parity setting is None=no parity, 0=even, 1=odd
        self.uart = UART(uart, baudrate=100000, parity=0, stop=2, read_buf_len=256)

        # TODO: check if uart really has to be disabled to set invert

        print()
        print(f"USART1:    0x{stm.USART1:08X}")
        print(f"USART3:    0x{stm.USART3:08X}")
        print(f"USART_CR1: {stm.USART_CR1:d}")
        print(f"USART_CR2: {stm.USART_CR2:d}")


        if invert:
            # UART RX pin active level inversion is only supported on the STM32H743
            # (includes OpenMV Cam H7/H7 Plus)
            if platform not in ("OpenMV4-H7", "OpenMV4P-H7"):
                raise ValueError("RX pin level inversion not supported.")

            # Datasheet states RXINV can only be written when the USART is disabled (UE = 0)
            if uart == 1:
                stm.mem32[stm.USART1 + stm.USART_CR1] &= ~1         # disable USART (UE=0)
                stm.mem32[stm.USART1 + stm.USART_CR2] |= (1 << 16)  # set RXINV
                stm.mem32[stm.USART1 + stm.USART_CR1] |= 1          # re-enable USART (UE=1)

            elif uart == 3:
                stm.mem32[stm.USART3 + stm.USART_CR1] &= ~1         # disable USART (UE=0)
                stm.mem32[stm.USART3 + stm.USART_CR2] |= (1 << 16)  # set RXINV
                stm.mem32[stm.USART3 + stm.USART_CR1] |= 1          # re-enable USART (UE=1)

            else:
                # OpenMV Cam H7/H7 Plus only supports UART1 and UART3
                raise ValueError(f"RX pin level inversion not supported for UART({uart:d})")

        self.index = 0
        self.buffer = bytearray(25)
        self.data = 0

        self.pin1 = Pin('P9', Pin.OUT_PP)
        self.pin1.low()




    def read(self):
        """
        Read SBUS mesages.
        """
        new_data = False

        # TODO: pulse pin to check each message is captured
        while self.uart.any():
            new_data = new_data or self.parse_bytes()

        return new_data




    def parse_bytes(self):
        """
        Read byte(s) from UART and parse
        """
        retval = False

        while self.uart.any():

            b = ord(self.uart.read(1))

            if self.index == 0:
                if b == 0x0F:
                    self.buffer[0] = b
                    self.index = 1

            elif self.index > 0:
                self.buffer[self.index] = b
                self.index += 1

                if self.index > 24:
                    if b == 0x00:
                        # got complete, valid-looking message
                        # TODO: pulse pin to check each message is captured
                        # TODO: copy (actual copy) of data buffer, so it's always valid
                        retval = True
                        self.pin1.high()
                        self.pin1.low()
                    else:
                        # error occured while parsing, discard message
                        retval = False

                    self.index = 0

            else:
                self.index = 0

        return retval



    def get_channel(self, channel):
        """
        Convert and return only a single specific channel.
        This is more efficient that converting all channels all the time.

        Parameter:
            channel  Channel index

        Returns:
            Pulse length in us
        """
        bit_idx = channel*SBUS.BITSIZE
        value = 0

        for byte_idx in range((bit_idx+SBUS.BITSIZE)//8, bit_idx//8-1, -1):
            value = (value<<8) + self.buffer[byte_idx+1]
        value = (value>>(bit_idx%8)) & ((1<<SBUS.BITSIZE)-1)
        #return (((value-SBUS.OFFSET)*SBUS.SCALING)>>3) + SBUS.CENTER
        return value




    def get_channels(self):
        """
        Convert and return all SBUS channels

        Parameters:
            none

        Returns:
            list of pulse lengths in SBUS units
        """
        # TODO: check if this may be faster
        #self.data = int.from_bytes(self.buffer[1:23], "little")
        #for i in range(16):
        #    self.channels[i] = self.data & 0x7FF
        #    self.data = self.data >> 11
        ##    #print(self.channels[i])

        channels = [0]*SBUS.CHANNELS

        for i in range(0,SBUS.CHANNELS):

            bit_idx = i*SBUS.BITSIZE
            value = 0

            for byte_idx in range((bit_idx+SBUS.BITSIZE)//8, bit_idx//8-1, -1):
                value = (value<<8) + self.buffer[byte_idx+1]
                channels[i] = (value>>(bit_idx%8)) & ((1<<SBUS.BITSIZE)-1)
                channels[i] = (((channels[i]-SBUS.OFFSET)*SBUS.SCALING)>>3) + SBUS.CENTER
                #TODO: test us conversion (and optimize?)

        return channels



sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.VGA)
sensor.set_vflip(False)
sensor.set_hmirror(False)
sensor.set_auto_gain(False, gain_db=0)

sbus = SBUS(uart=1, invert=True)

t_start = micros()
t = 0
t_old = 0

print("ready...")


while True:

    img = sensor.snapshot()

    # TOOD: check what happens if we delay so much that we get a buffer overflow in the SBUS
    # input buffer. Does it recover? Is more buffer needed?

    if sbus.read():

        t_old = t
        t = elapsed_micros(t_start)

        ch6 = sbus.get_channel(5)
        ch7 = sbus.get_channel(6)
        ch13 = sbus.get_channel(12)

        print(f"{t-t_old:5d} us    CH6={ch6:4d}    CH7={ch7:4d}    CH13={ch13:4d}")
