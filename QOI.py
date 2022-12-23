def uint32(num: int):
    """
    returns a 4 byte bytearray representation of the input int as a uint32
    """
    assert type(num) == int, "input must be int"
    assert num >= 0, "input must be positive"
    assert num < 2**32, "input must be less than 2^32"
    binary_string = bin(num)[2:]
    binary_string = "0"*(32-len(binary_string)) + binary_string
    uint32_byte_array = bytearray([int(binary_string[0:8], base=2), int(binary_string[8:16], base=2), int(binary_string[16:24], base=2), int(binary_string[24:32], base=2)])

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


def closest_difference_wraparound(current: int, previous: int, wrap_range = (0, 255)):  # FIXME actually implement wrap_range
    """
    returns the signed absolute smallest difference (int, current-previous)
    with wraparound operation in wrap_range
    default range is (0, 255), that means 255 + 1 = 0
    """
    difference = int()

    normal_difference = current - previous
    top_wrap_difference = current - previous + 256  # previous is close to top, current is close to bottom
    bottom_wrap_difference = current - previous - 256  # previous is close to bottom, current is close to top

    absolute_normal_difference = abs(normal_difference)
    absolute_top_wrap_difference = abs(top_wrap_difference)
    absolute_bottom_wrap_difference = abs(bottom_wrap_difference)

    smallest_absolute = min([absolute_normal_difference, absolute_top_wrap_difference, absolute_bottom_wrap_difference])
    if smallest_absolute == absolute_normal_difference:
        difference = normal_difference
    elif smallest_absolute == absolute_top_wrap_difference:
        difference = top_wrap_difference
    else:
        difference = bottom_wrap_difference

    return difference


class Image():
    def __init__(self, x_dimension: int = 0, y_dimension: int = 0, mode_number_of_colors: str = "RGB", colorspace: int = 1):
        """
        x_dimension is the width of the image in pixels, y_dimension is the height of the image in pixels
        mode_number_of_colors is either "RGB" or "RGBA"
        colorspace is either 1 for all linear, or 0 for sRGB with linear alpha
        """
        assert type(x_dimension) == int and type(y_dimension) == int, "x_dimension and y_dimension must be defined and int"
        assert x_dimension > 0 and y_dimension > 0, "x_dimension and y_dimension must be strictly positive"
        assert mode_number_of_colors in ["RGB", "RGBA"], "mode_number_of_colors must be str RGB or RGBA"
        assert colorspace in [0, 1], "colorspace must be int 0 or 1"
        self.__pixel_list = []
        self.__mode_string = mode_number_of_colors
        self.__colorspace = colorspace
        self.__x_dimension = x_dimension
        self.__y_dimension = y_dimension

    def set_pixel_list(self, pixel_list: list):
        """
        call this method to add pixel data to the Image object.
        pixel_list is a list of lists, each sublist should have length of 3 for RGB mode, or 4 for RGBA mode
        each item in sublists must be an int 
        """
        assert type(pixel_list) == list, "input was not a list"
        assert len(pixel_list) == self.__x_dimension*self.__y_dimension, "len() was not x_dimension*y_dimension"
        assert all([type(i) == list for i in pixel_list]), "each item in list needs to be list"
        assert all([all([type(i) == int for i in ii]) for ii in pixel_list]), "each item in sublists needs to be int"
        if self.__mode_string == "RGB":
            assert all([len(i) == 3 for i in pixel_list]), "len of items in list needs to be 3 for RGB"
        else:
            assert all([len(i) == 4 for i in pixel_list]), "len of items in list needs to be 4 for RGBA"
        assert max([max(i) for i in pixel_list]) < 256, "max was larger than 255"
        assert min([min(i) for i in pixel_list]) >= 0, "min was less than 0"

        # FIXME assertations are incredibly slow

        self.__pixel_list = pixel_list

    def __check_encoding_methods(self, current_pixel_index: int, running_pixels_array: list):
        """
        as part of the encoding process,
        gets called for each pixel in the pixel list,
        checks which encoding methods are available to use for that pixel

        returns: a list of booleans: [OP_INDEX, OP_DIFF, OP_LUMA, OP_RUN]
        if an item is true that means that encoding method can be used
        """
        pixel = self.__pixel_list[current_pixel_index]
        if current_pixel_index > 0:
            previous_pixel = self.__pixel_list[current_pixel_index-1]
        else:
            previous_pixel = [0, 0, 0, 255]

        can_run = (pixel == previous_pixel)
        if can_run:
            # these are what can_ran being True implies
            is_in_running_pixels_array = True
            is_within_difference_range = True
            is_within_luma_range = True
            # then we don't need to check for any of those, which is the rest of them
        else:
            is_in_running_pixels_array = (pixel in running_pixels_array)
            if is_in_running_pixels_array:  # NOTE this will prevent other things from being checked
                is_within_difference_range = None
                is_within_luma_range = None
                # those can't be assumed but don't matter due to the order preference of the encoder
            else:
                difference_red, difference_green, difference_blue = [closest_difference_wraparound(pixel[i], previous_pixel[i]) for i in range(3)]
                is_within_difference_range = all([-2 <= difference_red <= 1,
                                                -2 <= difference_green <= 1,
                                                -2 <= difference_blue <= 1])
                if is_within_difference_range:
                    # this implies that it's within luma range, so that doesn't need to be checked
                    is_within_luma_range = True
                else:
                    is_green_within_luma_range = (-32 <= difference_green <= 31)
                    is_red_within_luma_range = False
                    is_blue_within_luma_range = False
                    if is_green_within_luma_range:  # avoid checking red and blue if green is already false
                        is_red_within_luma_range = (-8 <= closest_difference_wraparound(pixel[0], previous_pixel[0]+difference_green) <= 7)
                        if is_red_within_luma_range:  # avoid checking blue if red is already false
                            is_blue_within_luma_range = (-8 <= closest_difference_wraparound(pixel[2], previous_pixel[2]+difference_green) <= 7)
                    is_within_luma_range = all([is_green_within_luma_range, is_red_within_luma_range, is_blue_within_luma_range])

        return [is_in_running_pixels_array, is_within_difference_range, is_within_luma_range, can_run]

    def encode(self, filepathname: str):
        """
        this method takes the image stored in the object (don't forget to set pixels of the image with set_pixel_list())
        and encodes it using the QOI encoding algorithm,
        the resulting bytes are then written to filepathname.
        """
        assert type(self.__pixel_list) == list, "pixel list was not a list"
        assert len(self.__pixel_list) > 0, "pixel list was empty"
        if self.__mode_string == "RGB":
            mode_number_of_colors = 3
        else:
            mode_number_of_colors = 4

        # QOI 14-byte header
        file_header_bytes = bytearray("qoif", "UTF-8")
        file_header_bytes.extend(uint32(self.__x_dimension))
        file_header_bytes.extend(uint32(self.__y_dimension))
        file_header_bytes.extend(uint8(mode_number_of_colors))
        file_header_bytes.extend(uint8(self.__colorspace))

        # predefining variables needed inside for loop
        counts = [0, 0, 0, 0, 0]  # RGB(A), Array Index, Diff, Luma, Run
        image_bytes = bytearray()
        if self.__mode_string == "RGB":
            running_pixels_array = [[0, 0, 0] for _ in range(64)]  # check specification
        else:
            running_pixels_array = [[0, 0, 0, 0] for _ in range(64)]
        number_of_pixels = len(self.__pixel_list)
        run = 0

        # iterating through each pixel in the image
        for current_pixel_index in range(number_of_pixels):
            # printing progress for debugging
            if current_pixel_index % 10000 == 0:
                print("encoding: {:6.2f}%    \r".format(current_pixel_index/number_of_pixels*100), end="")

            if run > 0:  # if we are currently on a run of pixels, skip all pixels until after the run
                run -= 1
            else:
                pixel = self.__pixel_list[current_pixel_index]
                if current_pixel_index > 0:
                    previous_pixel = self.__pixel_list[current_pixel_index-1]
                else:
                    previous_pixel = [0, 0, 0, 255]

                # checking which encoding methods can be used for this pixel
                is_in_running_pixels_array, is_within_difference_range, is_within_luma_range, can_run = self.__check_encoding_methods(current_pixel_index, running_pixels_array)

                # if no compression method can be used, store RGB(A) pixel entirely
                if not any([is_in_running_pixels_array, is_within_difference_range, is_within_luma_range, can_run]):
                    counts[0] += 1
                    if self.__mode_string == "RGB":
                        image_bytes.extend(bytearray([int(254), int(pixel[0]), int(pixel[1]), int(pixel[2])]))
                    else:
                        image_bytes.extend(bytearray([int(255), int(pixel[0]), int(pixel[1]), int(pixel[2]), int(pixel[3])]))

                # if a run of pixels is possible, encode that
                elif can_run:
                    counts[4] += 1
                    still_same = True
                    max_index = len(self.__pixel_list)-1
                    run = 0
                    while still_same and run < 62:
                        run += 1
                        if current_pixel_index+run <= max_index:
                            if self.__pixel_list[current_pixel_index+run] != pixel:
                                still_same = False
                        else:
                            still_same = False
                            run -= 1  # set run to go till the last pixel in the image
                    image_bytes.extend(bytearray([int(192 + run-1)]))  # first two bits (flag) are 11, so number is run length (1-62) plus 128+64 = 192, bias of -1 on run (0 means run 1)
                    run -=1  # to count the current pixel being encoded

                # otherwise if the pixel is in the array of 64 pixels, encode that
                elif is_in_running_pixels_array:
                    counts[1] += 1
                    image_bytes.extend(bytearray([int(running_pixels_array.index(pixel))]))  # first two bits (flag) are 00, so number must be less than 64 (guaranteed from len(running_pixels_array))

                # otherwise if the pixel is within the small difference range, encode that
                elif is_within_difference_range:
                    counts[2] += 1
                    # -2 from previous pixel is stored as 0 (00), +1 is stored as 3 (11)
                    # 1-2 = 255, 255+1 = 0, wraparound
                    difference = [closest_difference_wraparound(pixel[c], previous_pixel[c]) for c in range(3)]
                    image_bytes.extend(bytearray([int(64 + (difference[0]+2)*16 + (difference[1]+2)*4 + (difference[2]+2))]))  # first two bits (flag) are 01, so we add 64, each next two bits is dr, dg, db, bias of 2

                # otherwise if the pixel is within the small luma range, encode that
                elif is_within_luma_range:  # could be replaced with else but kept for clarity
                    counts[3] += 1
                    difference_green = int()  # 6 bits (0-63), -32 stored as 0, 31 stored as 63
                    difference_red_from_green = int()  # 3 bits (0-15), -8 stored as 0, 7 stored as 15
                    difference_blue_from_green = int()  # 4 bits (0-15), -8 stored as 0, 7 stored as 15

                    difference_green = closest_difference_wraparound(pixel[1], previous_pixel[1])
                    difference_red_from_green = closest_difference_wraparound(pixel[0], previous_pixel[0]+difference_green)
                    difference_blue_from_green = closest_difference_wraparound(pixel[2], previous_pixel[2]+difference_green)
                    image_bytes.extend(bytearray([int(128 + (difference_green+32)), int((difference_red_from_green+8)*16 + (difference_blue_from_green+8))]))  # two bytes, first two bits (flag) are 10, so we add 128, then difference green in the first byte, bias of 32 for that one. second byte is difference red from green then difference blue from green, bias of 8 for each of those

                # update the array of 64 pixels
                if self.__mode_string == "RGB":
                    pixel_index_in_running_pixels = (pixel[0]*3 + pixel[1]*5 + pixel[2]*7 + 255*11) % 64
                else:
                    pixel_index_in_running_pixels = (pixel[0]*3 + pixel[1]*5 + pixel[2]*7 + pixel[3]*11) % 64
                running_pixels_array[pixel_index_in_running_pixels] = pixel
        # end of for loop iterating each pixel

        # QOI 8-byte end of file marker
        end_of_file_bytes = bytearray([0, 0, 0, 0, 0, 0, 0, 1])
        bytes_to_write = bytearray()
        bytes_to_write.extend(file_header_bytes)
        bytes_to_write.extend(image_bytes)
        bytes_to_write.extend(end_of_file_bytes)

        # write bytes to file
        self.__write_file(filepathname, bytes_to_write)

    def __write_file(self, filepathname: str, bytes: bytearray):
        """
        writes bytes to file filepathname
        """
        if not filepathname.endswith(".qoi"):
            filepathname += ".qoi"
        with open(filepathname, "wb") as file_writer:
            file_writer.write(bytes)

    def decode(self, file):
        """
        QOI decoder which writes the results to the Image object
        this overwrites any preexisting data in the Image object
        """
        pass


if __name__ == "__main__":
    from PIL import Image as IMG
    import os

    for path, directories, files in os.walk(os.curdir):
        for file in files:
            if file.lower().endswith(".png"):
                print("loading image {}...".format(file))
                try:
                    img = IMG.open(file)
                    pixel_list = [list(pixel_values) for pixel_values in list(img.getdata())]
                    dimensions = [img.width, img.height]
                    print("creating image object")
                    img = Image(dimensions[0], dimensions[1])
                    img.set_pixel_list(pixel_list)
                    print("encoding and writing...")
                    img.encode(file)
                except IMG.DecompressionBombError:
                    pass
