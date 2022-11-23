import bitio

def uint(num: int, digits: int):
    """
    returns a string binary representation of the input int as a uint32
    """
    assert type(num) == int, "input must be int"
    assert num >= 0, "input must be positive"
    assert num < 2**digits, "input must be less than 2^digits"
    assert type(digits) == int, "digits must be int"
    assert digits > 0, "digits must be positive"
    binary_string = bin(num)[2:]
    binary_string = "0"*(digits-len(binary_string)) + binary_string

    return binary_string

class Image():
    def __init__(self, dimx: int = None, dimy: int = None, mode: str = "RGB", space: int = 1):
        """
        dimx is the width of the image in pixels, dimy is the height of the image in pixels
        mode is either "RGB" or "RGBA"
        space is either 1 for all linear, or 0 for sRGB with linear alpha
        """
        assert type(dimx) == int and type(dimy) == int, "dimx and dimy must be defined and int"
        assert dimx > 0 and dimy > 0, "dimx and dimy must be strictly positive"
        assert mode in ["RGB", "RGBA"], "mode must be str RGB or RGBA"
        assert space in [0, 1], "space must be int 0 or 1"
        self.__pixel_list = None
        self.__mode = mode
        self.__space = space
        self.__dimx = dimx
        self.__dimy = dimy

    def set_pixel_list(self, pix_list: list):
        assert type(pix_list) == list, "input was not a list"
        assert len(pix_list) == self.__dimx*self.__dimy, "len() was not dimx*dimy"
        assert max(pix_list) < 256, "max was larger than 255"
        assert min(pix_list) >= 0, "min was less than 0"
        self.__pixel_list = pix_list

    def encode(self, file):
        assert type(self.__pixel_list) == list, "pixel list was not a list"
        assert len(self.__pixel_list) > 0, "pixel list was empty"
        if self.__mode == "RGB":
            mode = 3
        else:
            mode = 4
        file_header = bytearray("qoif", "UTF-8")
        file_header.extend(bytearray(uint(self.__dimx, 32), "UTF-8"))
        file_header.extend(bytearray(uint(self.__dimy, 32), "UTF-8"))
        file_header.extend(bytearray(uint(mode, 8), "UTF-8"))
        file_header.extend(bytearray(uint(self.__space, 8), "UTF-8"))
        # file header has been created according to QOI specification
        image_bytes = bytearray()
        running_pixels = [0 for _ in range(64)]
        for pixel in self.__pixel_list:
            tag = str()  # current chunk's tag, either 2 bit or 8 bit
            chunk_choice = str()  # one of RGB, RGBA, INDEX, DIFF, LUMA, RUN
            is_in_running_pixels = (pixel in running_pixels)
            


            running_pixels = running_pixels[1:]  # shift pixels over in the buffer
            running_pixels.append(pixel)  # add current pixel

        eof = bytearray([0, 0, 0, 0, 0, 0, 0, 1])  # QOIs end of file marker
        self.__write_file(file)

    def __write_file(self, file):
        pass

    def decode(self, file):
        pass


if __name__ == "__main__":
    img = Image(2, 2)
    img.set_pixel_list([0, 255, 128, 128])
    img.encode("file")
