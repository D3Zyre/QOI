import bitio


def uint32(num: int):
    """
    returns a 4 byte bytearray representation of the input int as a uint32
    """
    assert type(num) == int, "input must be int"
    assert num >= 0, "input must be positive"
    assert num < 2**32, "input must be less than 2^32"
    binary_string = bin(num)[2:]
    binary_string = "0"*(32-len(binary_string)) + binary_string
    uint32_byte_array = bytearray([int(binary_string[24:32], base=2), int(binary_string[16:24], base=2), int(binary_string[8:16], base=2), int(binary_string[0:8], base=2)])

    return uint32_byte_array


def uint8(num: int):
    """
    returns a 1 byte bytearray representation of the input int as a uint8
    """
    assert type(num) == int, "input must be int"
    assert num >= 0, "input must be positive"
    assert num < 2**8, "input must be less than 2^8"
    uint8_byte_array = bytearray([num])

    return uint8_byte_array


class Image():
    def __init__(self, x_dimension: int = None, y_dimension: int = None, mode_number_of_colors: str = "RGB", colorspace: int = 1):
        """
        x_dimension is the width of the image in pixels, y_dimension is the height of the image in pixels
        mode_number_of_colors is either "RGB" or "RGBA"
        colorspace is either 1 for all linear, or 0 for sRGB with linear alpha
        """
        assert type(x_dimension) == int and type(y_dimension) == int, "x_dimension and y_dimension must be defined and int"
        assert x_dimension > 0 and y_dimension > 0, "x_dimension and y_dimension must be strictly positive"
        assert mode_number_of_colors in ["RGB", "RGBA"], "mode_number_of_colors must be str RGB or RGBA"
        assert colorspace in [0, 1], "colorspace must be int 0 or 1"
        self.__pixel_list = None
        self.__mode_string = mode_number_of_colors
        self.__colorspace = colorspace
        self.__x_dimension = x_dimension
        self.__y_dimension = y_dimension

    def set_pixel_list(self, pix_list: list):
        assert type(pix_list) == list, "input was not a list"
        assert len(pix_list) == self.__x_dimension*self.__y_dimension, "len() was not x_dimension*y_dimension"
        assert all([type(i) == list for i in pix_list]), "each item in list needs to be list"
        if self.__mode_string == "RGB":
            assert all([len(i) == 3 for i in pix_list]), "len of items in list needs to be 3 for RGB"
        else:
            assert all([len(i) == 4 for i in pix_list]), "len of items in list needs to be 4 for RGBA"
        assert max([max(i) for i in pix_list]) < 256, "max was larger than 255"
        assert min([min(i) for i in pix_list]) >= 0, "min was less than 0"
        self.__pixel_list = pix_list

    def encode(self, filepathname: str):
        assert type(self.__pixel_list) == list, "pixel list was not a list"
        assert len(self.__pixel_list) > 0, "pixel list was empty"
        if self.__mode_string == "RGB":
            mode_number_of_colors = 3
        else:
            mode_number_of_colors = 4
        file_header_bytes = bytearray("qoif", "UTF-8")  # QOIs file header
        file_header_bytes.extend(uint32(self.__x_dimension))
        file_header_bytes.extend(uint32(self.__y_dimension))
        file_header_bytes.extend(uint8(mode_number_of_colors))
        file_header_bytes.extend(uint8(self.__colorspace))
        # file header has been created according to QOI specification
        counts = [0, 0, 0, 0, 0] # RGB(A), Array Index, Diff, Luma, Run
        image_bytes = bytearray()
        running_pixels_array = [0 for _ in range(64)]  # check specification
        run = 0
        for current_pixel_index in range(len(self.__pixel_list)):  # TODO some optimization to be done here, avoid doing unnecessary computations
            if run > 0:
                run -= 1
            else:
                pixel = self.__pixel_list[current_pixel_index]
                is_in_running_pixels_array = (pixel in running_pixels_array)
                is_within_difference_range = all([-2 <= pixel[i]-self.__pixel_list[current_pixel_index-1][i] <= 1 or -2 <= pixel[i]+256-self.__pixel_list[current_pixel_index-1][i] <= 1 or -2 <= pixel[i]-256-self.__pixel_list[current_pixel_index-1][i] <= 1 for i in range(3)])  # check with wraparound
                is_green_within_luma_range = -32 <= pixel[1]-self.__pixel_list[current_pixel_index-1][1] <= 31 or -32 <= pixel[1]+256-self.__pixel_list[current_pixel_index-1][1] <= 31 or -32 <= pixel[1]-256-self.__pixel_list[current_pixel_index-1][1] <= 31
                is_red_within_luma_range = False
                is_blue_within_luma_range = False
                if is_green_within_luma_range:
                    green_luma_difference = pixel[1] - self.__pixel_list[current_pixel_index-1][1]
                    if green_luma_difference < -32:  # previous pixel was 255 or something
                        green_luma_difference += 256
                    elif green_luma_difference > 31:  # current pixel is 255 or something
                        green_luma_difference -= 256
                    is_red_within_luma_range = -8 <= pixel[0]-self.__pixel_list[current_pixel_index-1][0]-green_luma_difference <= 7 or -8 <= pixel[0]+256-self.__pixel_list[current_pixel_index-1][0]-green_luma_difference <= 7 or -8 <= pixel[0]-256-self.__pixel_list[current_pixel_index-1][0]-green_luma_difference <= 7
                    if is_red_within_luma_range:
                        is_blue_within_luma_range = -8 <= pixel[2]-self.__pixel_list[current_pixel_index-1][2]-green_luma_difference <= 7 or -8 <= pixel[2]+256-self.__pixel_list[current_pixel_index-1][2]-green_luma_difference <= 7 or -8 <= pixel[2]-256-self.__pixel_list[current_pixel_index-1][2]-green_luma_difference <= 7
                is_within_luma_range = all([is_green_within_luma_range, is_red_within_luma_range, is_blue_within_luma_range])
                can_run = (pixel == self.__pixel_list[current_pixel_index-1])
                # above checks which encoding style can be used
                if not any([is_in_running_pixels_array, is_within_difference_range, is_within_luma_range, can_run]):
                    counts[0] += 1
                    # if none of the methods work, we have to story in RGB/RGBA directly
                    if self.__mode_string == "RGB":
                        image_bytes.extend(bytearray([int(254), int(pixel[0]), int(pixel[1]), int(pixel[2])]))
                    else:
                        image_bytes.extend(bytearray([int(255), int(pixel[0]), int(pixel[1]), int(pixel[2]), int(pixel[3])]))
                elif can_run:
                    counts[4] += 1
                    still_same = True
                    max_index = len(self.__pixel_list)-1
                    run = 0
                    while still_same and run < 63:
                        run += 1
                        if not current_pixel_index+run > max_index and self.__pixel_list[current_pixel_index+run] != pixel:
                            still_same = False
                    image_bytes.extend(bytearray([int(192 + run-1)]))  # first two bits (flag) are 11, so number is run length (1-62) plus 128+64 = 192, bias of -1 on run (0 means run 1)
                elif is_in_running_pixels_array:
                    counts[1] += 1
                    image_bytes.extend(bytearray([int(running_pixels_array.index(pixel))]))  # first two bits (flag) are 00, so number must be less than 64 (guaranteed from len(running_pixels_array))
                elif is_within_difference_range:
                    counts[2] += 1
                    # -2 from previous pixel is stored as 0 (00), +1 is stored as 3 (11)
                    # 1-2 = 255, 255+1 = 0, wraparound
                    difference = [0, 0, 0]
                    for c in range(3):
                        difference[c] = pixel[c] - self.__pixel_list[current_pixel_index-1][c]
                        if difference[c] < -2:  # previous pixel was 255 or something
                            difference[c] += 256
                        elif difference[c] > 1:  # current pixel is 255 or something
                            difference[c] -= 256
                    image_bytes.extend(bytearray([int(64 + (difference[0]+2)*16 + (difference[1]+2)*4 + (difference[2]+2))]))  # first two bits (flag) are 01, so we add 64, each next two bits is dr, dg, db, bias of 2
                elif is_within_luma_range:  # could be replaced with else but kept for clarity
                    counts[3] += 1
                    difference_green = int()  # 6 bits (0-63), -32 stored as 0, 31 stored as 63
                    difference_red_from_green = int()  # 3 bits (0-15), -8 stored as 0, 7 stored as 15
                    difference_blue_from_green = int()  # 4 bits (0-15), -8 stored as 0, 7 stored as 15
                    difference_green = green_luma_difference  # previously calculated
                    difference_red_from_green = pixel[0] - self.__pixel_list[current_pixel_index-1][0]-difference_green
                    if difference_red_from_green < -8:  # previous pixel was 255 or something
                        difference_red_from_green += 256
                    elif difference_red_from_green > 7:  # current pixel is 255 or something
                        difference_red_from_green -= 256
                    difference_blue_from_green = pixel[2] - self.__pixel_list[current_pixel_index-1][2]-difference_green
                    if difference_blue_from_green < -8:  # previous pixel was 255 or something
                        difference_blue_from_green += 256
                    elif difference_blue_from_green > 7:  # current pixel is 255 or something
                        difference_blue_from_green -= 256
                    image_bytes.extend(bytearray([int(128 + (difference_green+32)), int((difference_red_from_green+8)*16 + (difference_blue_from_green+8))]))  # two bytes, first two bits (flag) are 10, so we add 128, then difference green in the first byte, bias of 32 for that one. second byte is difference red from green then difference blue from green, bias of 8 for each of those
                if self.__mode_string == "RGB":
                    pixel_index_in_running_pixels = (pixel[0]*3 + pixel[1]*5 + pixel[2]*7) % 64
                else:
                    pixel_index_in_running_pixels = (pixel[0]*3 + pixel[1]*5 + pixel[2]*7 + pixel[3]*11) % 64
                running_pixels_array[pixel_index_in_running_pixels] = pixel

        print(counts)  # DEBUG

        end_of_file_bytes = bytearray([0, 0, 0, 0, 0, 0, 0, 1])  # QOIs end of file marker
        bytes_to_write = bytearray()
        bytes_to_write.extend(file_header_bytes)
        bytes_to_write.extend(image_bytes)
        bytes_to_write.extend(end_of_file_bytes)
        self.__write_file(filepathname, bytes_to_write)

    def __write_file(self, filepathname: str, bytes: bytearray):
        if not filepathname.endswith(".qoi"):
            filepathname += ".qoi"
        with open(filepathname, "wb") as file_writer:
            file_writer.write(bytes)

    def decode(self, file):
        pass


if __name__ == "__main__":
    from PIL import Image as IMG

    print("loading image...")
    img = IMG.open("IMG.BMP")
    pixel_list = [list(pixel_values) for pixel_values in list(img.getdata())]
    dimensions = [img.width, img.height]
    print("creating image object")
    img = Image(dimensions[0], dimensions[1])
    img.set_pixel_list(pixel_list)
    print("encoding and writing...")
    img.encode("file")
