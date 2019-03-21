# Standard library imports
import struct
import logging

# third party imports
import numpy as np
import imageio


class PhantomImage:
    """
    This class wraps functionality for dealing with phantom images. Most importantly the function to convert images
    to and from different file formats, including the protocol specific transmission formats

    CHANGELOG

    Added 23.02.2019

    Changed 20.03.2019
    Checking the edge case of what happens when the passed array is one dimensional.
    """

    def __init__(self, array):
        self.array = array

        # 20.03.2019
        # In case a one dimensional array is being passed it is being interpreted that the y axis is just 1 pixel wide
        if len(array.shape) == 1:
            self.resolution = (array.shape[0], 1)
        else:
            self.resolution = (array.shape[0], array.shape[1])

    # ###############################
    # CONVERSION TO DIFFERENT FORMATS
    # ###############################

    def to_transfer_format(self, fmt):
        _methods = {
            272:    self.p16,
            -272:   self.p16,
            8:      self.p8,
            -8:     self.p8,
            266:    self.p10,
            'P16':  self.p16,
            'P16R': self.p16,
            'P8':   self.p8,
            'P8R':  self.p8,
            'P10':  self.p10
        }
        return _methods[fmt]()

    def p16(self):
        """
        Converts the image to the P16 transfer format, which is essentially just a long byte string, with two bytes for
        each pixel in the image.

        CHANGELOG

        Added 23.02.2019

        Changed 18.03.2019
        Switched to using the struct packing to handle the byte strings.

        :return:
        """
        byte_buffer = []
        with np.nditer(self.array, op_flags=['readwrite'], order='C') as it:
            for x in it:

                # 18.03.2019
                # The format "<" tells that it is little endian byte order and "H" is for short, the datatype with
                # 2 bytes aka 16 bit.
                pixel_bytes = struct.pack('<H', x)
                byte_buffer.append(pixel_bytes)
        return b''.join(byte_buffer)

    def p8(self):
        """
        Converts the image to the P8 transfer format, which is essentially just a long byte string, with ONE byte
        (8 Bit) for each pixel in the image.

        CHANGELOG

        Added 26.02.2019

        Changed 18.03.2019
        Switched to using the struct packing to handle the byte strings.

        :return:
        """
        byte_buffer = []
        with np.nditer(self.array, op_flags=['readwrite'], order='C') as it:
            for x in it:

                # 18.03.2019
                # The format ">" stands for big endian byte order and "B" is for "unsigned char" data type, which has
                # 1 byte aka 8 bit.
                pixel_bytes = struct.pack('>B', x)
                byte_buffer.append(pixel_bytes)
        return b''.join(byte_buffer)

    def p10(self):
        """
        Converts the image to the P10 transfer format.

        CHANGELOG

        Added 26.02.2019

        :return:
        """
        byte_buffer = []
        with np.nditer(self.array, op_flags=['readwrite'], order='C') as it:

            values = list(it)
            for i in range(0, len(values), 3):
                temp = values[i:i+3]
                final_value = 0
                for value in temp:
                    final_value |= value
                    final_value <<= 10
                final_value >>= 10
                final_value <<= 2

                byte = struct.pack('!L', final_value)
                byte_buffer.append(byte)

        return b''.join(byte_buffer)

    # #############
    # CLASS METHODS
    # #############

    @classmethod
    def from_jpeg(cls, file_path):
        """
        Given the path to a JPEG image file, this method will open the image and convert it into a numpy matrix, from
        which a new PhantomImage object is created. This PhantomImage object is returned.

        CHANGELOG

        Added 23.02.2019

        :param file_path:
        :return: PhantomImage
        """
        array = imageio.imread(file_path, pilmode='L')
        return cls(array)

    @classmethod
    def from_p16(cls, raw_bytes, resolution):
        """
        Given a byte string a resolution tuple of two ints, this method will convert it into a PhantomImage object and
        return that.

        CHANGELOG

        Added 23.02.2019

        Changed 18.03.2019
        Switched to using the struct packing to handle the byte strings.

        :param raw_bytes:
        :param resolution:
        :return: PhantomImage
        """
        pixels = []
        for i in range(0, len(raw_bytes), 2):
            bytes_16 = raw_bytes[i:i+2]

            # 18.03.2019
            # The format '<' tells, that it is little endian byte order and "H" is for "short", the datatype with
            # 2 bytes aka 16 bit.
            value = struct.unpack('<H', bytes_16)[0]
            pixels.append(value)
        array = np.array(pixels)
        array = array.reshape(resolution)
        return cls(array)

    @classmethod
    def from_p8(cls, raw_bytes, resolution):
        """
        Given a byte string a resolution tuple of two ints, this method will convert it into a PhantomImage object and
        return that.

        CHANGELOG

        Added 26.02.2019

        :param raw_bytes:
        :param resolution:
        :return:
        """
        pixels = []
        for byte in raw_bytes:
            pixels.append(byte)
        array = np.array(pixels)
        array = array.reshape(resolution)
        return cls(array)

    @classmethod
    def from_p10(cls, raw_bytes, resolution):
        """
        Converts the raw bytes in p10 format into PhantomImage object

        CHANGELOG

        Added 26.02.2019

        Changed 18.03.2019
        Switched to using the struct packing to handle the byte strings.

        :param raw_bytes:
        :param resolution:
        :return:
        """
        mask = 0b1111111111
        pixels = []

        index = 0
        while index < len(raw_bytes):
            _bytes = raw_bytes[index:index+20]
            bytes_value = int.from_bytes(_bytes, 'big')
            _temp = []
            for i in range(16):
                value = bytes_value & mask
                _temp.append(value)
                bytes_value >>= 10
            pixels += reversed(_temp)
            index += 20

        """
        for i in range(0, len(raw_bytes), 4):
            bits_32 = raw_bytes[i:i+4]

            # 18.03.2019
            # The format '>' tells that it is big endian byte order and the 'L' is for the "long" datatype which is
            # 4 byte aka 32 bit
            value = struct.unpack('!L', bits_32)[0]
            value >>= 2

            mask = 0b1111111111
            for i in range(0, 3, 1):
                pixel_value = (value >> 10 * i) & mask
                pixels.append(pixel_value)
        """

        array = np.array(pixels)
        array = array.reshape(resolution)
        return cls(array)

    @classmethod
    def from_transfer_format(cls, fmt, raw_bytes, resolution):
        """
        Given the raw bytes string received from the socket and the resolution of the image, this method will create
        a new PhantomImage object from that information using the format identified by the given string format token
        name "fmt"

        CHANGELOG

        Added 28.02.2019

        :param fmt:
        :param raw_bytes:
        :param resolution:
        :return:
        """
        _methods = {
            'P16':          cls.from_p16,
            'P16R':         cls.from_p16,
            'P8':           cls.from_p8,
            'P8R':          cls.from_p8,
            'P10':          cls.from_p10
        }
        inverse_resolution = (resolution[1], resolution[0])
        return _methods[fmt](raw_bytes, inverse_resolution)

    @classmethod
    def random(cls, resolution):
        """
        Creates random PhantomImage.

        CHANGELOG

        Added 18.03.2019

        :param resolution:
        :return:
        """
        # This will create the correct base array, which only contains regular 8 bit pixel values (range 0 to 256)
        random_array = np.random.randint(0, 256, resolution)
        # Creating a new PhantomImage object from this array and then returning the Image object
        return cls(random_array)

    # ##############
    # HELPER METHODS
    # ##############

    @classmethod
    def downscale(cls, array, bits=8):
        """
        This method takes an array, which represents an image and scales all the values down to the range between 0
        and 128, which is needed to save the image in the common formats such as jpeg etc.

        :param array:
        :param bits:
        :return:
        """
        downscaled_array = array
        downscaled_array /= np.max(array)
        downscaled_array *= 2**(bits - 1)
        return downscaled_array
