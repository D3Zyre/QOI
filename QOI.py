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
        assert all([type(i) == list for i in pix_list]), "each item in list needs to be list"
        if self.__mode == "RGB":
            assert all([len(i) == 3 for i in pix_list]), "len of items in list needs to be 3 for RGB"
        else:
            assert all([len(i) == 4 for i in pix_list]), "len of items in list needs to be 4 for RGBA"
        assert max([max(i) for i in pix_list]) < 256, "max was larger than 255"
        assert min([min(i) for i in pix_list]) >= 0, "min was less than 0"
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
        for px in range(self.__pixel_list):
            pixel = self.__pixel_list[px]
            is_in_running_pixels = (pixel in running_pixels)
            is_within_diff_range = all([-2 <= pixel[i]-self.__pixel_list[px-1][i] <= 1  or -2 <= pixel[i]+256-self.__pixel_list[px-1][i] <= 1 or -2 <= pixel[i]-256-self.__pixel_list[px-1][i] <= 1 for i in range(mode)])  # check with wraparound
            is_within_luma_range = None  # TODO/FIXME
            can_run = (pixel == self.__pixel_list[px-1])
            # above checks which encoding style can be used
            if any([is_in_running_pixels, is_within_diff_range, is_within_luma_range, can_run]) is False:
                # if none of the methods work, we have to story in RGB/RGBA directly
                if self.__mode == "RGB":
                    image_bytes.extend(bytearray([int(254), int(pixel[0]), int(pixel[1], int(pixel[2]))]))
                else:
                    image_bytes.extend(bytearray([int(255), int(pixel[0]), int(pixel[1], int(pixel[2])), int(pixel[3])]))
            elif can_run:
                still_same = True
                run = 0
                while still_same and run < 63:  # BUG/FIXME when doing run, we need to skip those pixels after
                    run += 1
                    if self.__pixel_list(px+run) != pixel:
                        still_same = False
                image_bytes.extend(bytearray([int(192 + run-1)]))  # first two bits (flag) are 11, so number is run length (1-62) plus 128+64 = 192, bias of -1 on run (0 means run 1)
            elif is_in_running_pixels:
                image_bytes.extend(bytearray([int(running_pixels.index(pixel))]))  # first two bits (flag) are 00, so number must be less than 64 (guaranteed from len(running_pixels))
            elif is_within_diff_range:
                # -2 from previous pixel is stored as 0 (00), +1 is stored as 3 (11)
                # 1-2 = 255, 255+1 = 0, wraparound
                diff = [0, 0, 0]
                for c in range(3):
                    diff[c] = pixel[c] - self.__pixel_list[px-1][c]
                    if diff < 0:  # previous pixel was 255 or something
                        diff[c] += 256
                    elif diff > 1:  # current pixel is 255 or something
                        diff[c] -= 256
                image_bytes.extend(bytearray([int(64 + (diff[0]+2)*16 + (diff[1]+2)*4 + (diff[2]+2))]))  # first two bits (flag) are 01, so we add 64, each next two bits is dr, dg, db, bias of -2
            elif is_within_luma_range:
                pass # TODO/FIXME
            if self.__mode == "RGB":
                pix_index = (pixel[0]*3 + pixel[1]*5 + pixel[2]*7) % 64
            else:
                pix_index = (pixel[0]*3 + pixel[1]*5 + pixel[2]*7 + pixel[3]*11) % 64
            running_pixels[pix_index] = pixel

        eof = bytearray([0, 0, 0, 0, 0, 0, 0, 1])  # QOIs end of file marker
        self.__write_file(file)

    def __write_file(self, file):
        pass

    def decode(self, file):
        pass


if __name__ == "__main__":
    img = Image(2, 2)
    img.set_pixel_list([[0, 0, 0], [255, 255, 255], [128, 128, 128], [128, 128, 128]])
    img.encode("file")
