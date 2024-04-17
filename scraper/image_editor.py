import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


class ImageProcessingError(Exception):
    pass


def add_text_to_image_with_strikethrough(
    in_file_path: str,
    out_file_path: str,
    font_path: str,
    text: str,
    text_size,
    text_position,
    strikethrough_line_index: int,
    strikethrough_text: str,
):
    # Check if the output directory exists
    output_directory = os.path.dirname(out_file_path)
    if not os.path.exists(output_directory):
        raise ImageProcessingError(
            f"Output directory does not exist: {output_directory}"
        )

    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Error processing font file: {font_path}")

    try:
        # Open the image and ensure the file is properly closed using a context manager
        with Image.open(in_file_path) as image:
            # Convert the image to RGB mode (if it's in RGBA format)
            image = image.convert("RGB")

            # Get the DPI value
            dpi = image.info.get("dpi")

            # Create a drawing object to add text
            draw = ImageDraw.Draw(image)
            font = ImageFont.truetype(font_path, text_size)
            line_gap = 4

            # lines = text.splitlines()
            # strike_through_width = draw.textlength(
            #     lines[strike_through_line_index], font=font
            # )
            strikethrough_width = draw.textlength(strikethrough_text, font=font)
            text_height = text_size

            draw.text(
                text_position, text, font=font, fill=(0, 0, 0), spacing=line_gap
            )

            # position (x, y)
            start_y = (
                text_position[1]
                + (text_height + line_gap) * strikethrough_line_index
                + text_size // 2
            )
            start_pos = (
                text_position[0],
                start_y,
            )
            end_pos = (
                text_position[0] + strikethrough_width,
                start_y,
            )
            draw.line([start_pos, end_pos], fill=(0, 0, 0), width=5)

            # Save the modified image
            image.save(out_file_path, dpi=dpi)
            print(f"Saved modified image as: {out_file_path}")

    except (OSError, IOError, SyntaxError) as e:
        raise ImageProcessingError(f"Error processing image: {e}")


# Add text to an image (JPEG or PNG) and save the output as a JPEG file
def add_text_to_image(
    in_file_path: str,
    out_file_path: str,
    font_path: str,
    text: str,
    size,
    position,
):
    # Check if the output directory exists
    output_directory = os.path.dirname(out_file_path)
    if not os.path.exists(output_directory):
        raise ImageProcessingError(
            f"Output directory does not exist: {output_directory}"
        )

    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Error processing font file: {font_path}")

    try:
        # Open the image and ensure the file is properly closed using a context manager
        with Image.open(in_file_path) as image:
            # Convert the image to RGB mode (if it's in RGBA format)
            image = image.convert("RGB")

            # Get the DPI value
            dpi = image.info.get("dpi")

            # Create a drawing object to add text
            draw = ImageDraw.Draw(image)
            font = ImageFont.truetype(font_path, size)

            # Draw text on the image
            draw.text(position, text, font=font, fill=(0, 0, 0))

            # Save the modified image
            image.save(out_file_path, dpi=dpi)
            print(f"Saved modified image as: {out_file_path}")

    except (FileNotFoundError, OSError, IOError, SyntaxError) as e:
        raise ImageProcessingError(f"Error processing image: {e}")


def append_text_to_filename(file_path, text) -> str:
    directory, filename = os.path.split(file_path)
    name, extension = os.path.splitext(filename)
    new_filename = name + text + extension
    new_file_path = os.path.join(directory, new_filename)
    return str(new_file_path)


def get_image_size(image_path):
    with Image.open(image_path) as image:
        width, height = image.size
        return width, height


def delete_image(image_path):
    try:
        os.remove(image_path)
        print(f"Image deleted: {image_path}")
    except FileNotFoundError:
        raise ImageProcessingError(f"Image not found: {image_path}")
    except OSError as e:
        raise ImageProcessingError(f"Error occurred while deleting image: {e}")


def change_file_extension(file_path, new_extension) -> str:
    # Get the directory path and filename from the file path
    directory, filename = os.path.split(file_path)

    # Get the original file extension
    _, old_extension = os.path.splitext(filename)

    # Replace the original file extension with the new extension
    new_filename = filename.replace(old_extension, new_extension)

    # Combine the new filename with the directory path
    new_file_path = os.path.join(directory, new_filename)

    return str(new_file_path)


def expand_and_center_image(
    image_path,
    output_path,
    new_size: tuple[int, int],
    background_color: tuple[int, int, int] = (255, 255, 255),
    min_dpi=300,
):
    """
    Expand the image to the new size with a specified background color and center the original image.

    Parameters:
        image_path (str): Path to the original image.
        output_path (str): Path to save the new image.
        new_size (tuple): New size of the image in the format (width, height).
        background_color (tuple, optional): Background color as an RGB tuple
                                            (default is white - (255, 255, 255)).
        min_dpi (int): minimum DPI for output file (default is 300)

    Raises:
        ImageProcessingError: If there are any errors during image processing.
    """

    try:
        # Open the original image using a context manager
        with Image.open(image_path) as image:
            # Convert the image to RGB mode if it is in RGBA format (PNG file)
            image = image.convert("RGB")

            # Get the DPI value and ensure it meets the minimum requirement
            dpi = image.info.get("dpi", (min_dpi, min_dpi))
            dpi = (max(dpi[0], min_dpi), max(dpi[1], min_dpi))

            # Get the size of the original image and the new image
            original_size = image.size
            new_width, new_height = new_size

            # Create a new blank image and fill it with the specified background color
            new_image = Image.new("RGB", new_size, background_color)

            # Calculate the placement position of the original image in the new image to keep it centered
            offset = (
                (new_width - original_size[0]) // 2,
                (new_height - original_size[1]) // 2,
            )

            # Paste the original image onto the center of the new image
            new_image.paste(image, offset)

            # Save the new image
            new_image.save(output_path, dpi=dpi)

    except FileNotFoundError:
        raise ImageProcessingError(f"Invalid image path: {image_path}")
    except OSError as e:
        raise ImageProcessingError(f"Error processing image: {e}")


def resize_for_ig_story(
    input_file_path: str, image_background_color: tuple[int, int, int]
):
    width, height = get_image_size(input_file_path)
    aspect_ratio = width / height

    # Resize image for IG Stories (9:16) maintaining the original aspect ratio.
    target_aspect_ratio = 9 / 16

    if aspect_ratio > target_aspect_ratio:
        # Original image is wider, so we use the width for resizing
        new_width = width
        new_height = int(width / target_aspect_ratio)
    else:
        # Original image is taller, so we use the height for resizing
        new_height = height
        new_width = int(height * target_aspect_ratio)

    if new_width < 800:
        new_width = 800
        new_height = int(new_width / target_aspect_ratio)

    try:
        expand_and_center_image(
            input_file_path,
            input_file_path,
            (new_width, new_height),
            image_background_color,
        )
    except (FileNotFoundError, OSError, ImageProcessingError) as e:
        print(f"Resize the image error: {e}")
        raise

    return new_width, new_height


def insert_text_to_ig_story(
    input_file_path: str,
    font_path: str,
    insert_text: str,
    strikethrough_line_index: int = None,
    strikethrough_text: str = None,
):
    width, height = get_image_size(input_file_path)

    image_width_to_text_ratio = 29
    text_size = round(width / image_width_to_text_ratio)

    image_width_to_text_position_x_ratio = 30.53
    image_height_to_text_position_y_ratio = 7.3
    text_position = (
        round(width / image_width_to_text_position_x_ratio),
        round(height / image_height_to_text_position_y_ratio),
    )
    try:
        if strikethrough_line_index is None:
            add_text_to_image(
                input_file_path,
                input_file_path,
                font_path,
                insert_text,
                text_size,
                text_position,
            )
        else:
            add_text_to_image_with_strikethrough(
                input_file_path,
                input_file_path,
                font_path,
                insert_text,
                text_size,
                text_position,
                strikethrough_line_index,
                strikethrough_text,
            )

    except (FileNotFoundError, ImageProcessingError) as e:
        print(f"Insert text to IG story image error:  {e}")
        raise


def ig_story_image_processing(
    input_file_path: str,
    image_background_color: tuple[int, int, int],
    font_path: str,
    insert_text: str,
    strikethrough_line_index: int = None,
    strikethrough_text: str = None,
):
    print("IG Story Image processing")

    resize_for_ig_story(input_file_path, image_background_color)
    insert_text_to_ig_story(
        input_file_path,
        font_path,
        insert_text,
        strikethrough_line_index,
        strikethrough_text,
    )

    print("IG Story Image processing completed")


# Example usage
def example() -> None:
    try:
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_path = os.path.join(
            app_dir, "fonts", "SourceSerifPro-SemiBold.ttf"
        )
        if not os.path.exists(font_path):
            print(f"Font file not found: {font_path}")
            return

        insert_text = "0 Hello!\n1 Space\n2 This is the third line of text."
        size = 40
        position = (30, 10)

        input_file_path = os.path.join(app_dir, "image_sample", "lightning.jpg")
        output_file_path = append_text_to_filename(input_file_path, "_mod")
        add_text_to_image(
            input_file_path,
            output_file_path,
            font_path,
            insert_text,
            size,
            position,
        )

        strike_through_index = 2
        strike_through_text = "2 This is"

        input_file_path = os.path.join(app_dir, "image_sample", "astronaut.png")
        output_file_path = change_file_extension(
            append_text_to_filename(input_file_path, "_mod"), ".jpg"
        )
        add_text_to_image_with_strikethrough(
            input_file_path,
            output_file_path,
            font_path,
            insert_text,
            size,
            position,
            strike_through_index,
            strike_through_text,
        )

    except (Exception, ImageProcessingError) as e:
        print(f"Error occurred during image processing: {e}")


def create_ig_story_image_example(
    image_path: str, insert_text: str = ""
) -> None:
    try:
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_path = os.path.join(
            app_dir, "fonts", "SourceSerifPro-SemiBold.ttf"
        )
        if not os.path.exists(font_path):
            print(f"Font file not found: {font_path}")
            return

        width, height = get_image_size(image_path)

        # Resize image for IG Stories (9:16).
        new_height = int(width * (16 / 9))

        image_width_to_text_ratio = 29
        text_size = round(width / image_width_to_text_ratio)

        image_width_to_text_position_x_ratio = 30.53
        image_height_to_text_position_y_ratio = 7.3
        text_position = (
            round(width / image_width_to_text_position_x_ratio),
            round(new_height / image_height_to_text_position_y_ratio),
        )

        output_file_path = append_text_to_filename(image_path, "_ig_story")

        expand_and_center_image(
            image_path, output_file_path, (width, new_height)
        )

        add_text_to_image(
            output_file_path,
            output_file_path,
            font_path,
            insert_text,
            text_size,
            text_position,
        )

    except (Exception, ImageProcessingError) as e:
        print(f"Error occurred during image processing: {e}")


def generate_gray_image(width=256, height=256) -> None:
    gray_list = []

    # Generate the grayscale values from 0 to 255
    for y in range(height):
        row = []
        for x in range(width):
            # Calculate the grayscale value based on the x and y positions
            value = (y * width + x) % 256
            row.append(value)
        gray_list.append(row)

    # Convert the 2D list to a NumPy array
    gray_data = np.array(gray_list, dtype=np.uint8)

    # Show grayscale image
    cv2.imshow("Gray Image", gray_data)

    key = cv2.waitKey(0)
    if key == ord("s"):
        image_name = "gray_image.png"
        print(f"Save grayscale image: {image_name}")
        cv2.imwrite(image_name, gray_data)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    # generate_gray_image()

    example()

    # app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # image_path = os.path.join(app_dir, "image_sample", "lightning.jpg")
    # create_ig_story_image_example(image_path, "Lightning")
