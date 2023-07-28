import os

from PIL import Image, ImageDraw, ImageFont


class ImageProcessingError(Exception):
    pass


# Add text to an image (JPEG or PNG) and save the output as a JPEG file
def add_text_to_image(in_file_path: str, out_file_path: str, text: str, size, position):
    if not isinstance(in_file_path, str):
        raise ImageProcessingError(f"Invalid 'in_file_path' parameter. Expected string, got {type(in_file_path)}")
    if not isinstance(out_file_path, str):
        raise ImageProcessingError(f"Invalid 'in_file_path' parameter. Expected string, got {type(out_file_path)}")
    if not isinstance(text, str):
        raise ImageProcessingError(f"Invalid 'text' parameter. Expected string, got {type(text)}")

    # Check if the output directory exists
    output_directory = os.path.dirname(out_file_path)
    if not os.path.exists(output_directory):
        raise ImageProcessingError(f"Output directory does not exist: {output_directory}")

    try:
        image = Image.open(in_file_path)
    except (FileNotFoundError, OSError):
        raise ImageProcessingError(f"Invalid image path: {in_file_path}")

    # Convert the image to RGB mode if it is in RGBA format (PNG file)
    image = image.convert("RGB")

    dpi = image.info.get("dpi")

    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("SourceSerifPro-SemiBold.ttf", size)

    draw.text(position, text, font=font, fill=(0, 0, 0))

    image.save(out_file_path, dpi=dpi)
    print(f"Saved modified image as: {out_file_path}")


def append_text_to_filename(file_path, text):
    directory, filename = os.path.split(file_path)
    name, extension = os.path.splitext(filename)
    new_filename = name + text + extension
    new_file_path = os.path.join(directory, new_filename)
    return new_file_path


def get_image_size(image_path):
    image = Image.open(image_path)
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


def change_file_extension(file_path, new_extension):
    # Get the directory path and filename from the file path
    directory, filename = os.path.split(file_path)

    # Get the original file extension
    _, old_extension = os.path.splitext(filename)

    # Replace the original file extension with the new extension
    new_filename = filename.replace(old_extension, new_extension)

    # Combine the new filename with the directory path
    new_file_path = os.path.join(directory, new_filename)

    return new_file_path


def expand_and_center_image(image_path, output_path, new_size, background_color=(255, 255, 255)):
    """
    Expand the image to the new size with a specified background color and center the original image.

    Parameters:
        image_path (str): Path to the original image.
        output_path (str): Path to save the new image.
        new_size (tuple): New size of the image in the format (width, height).
        background_color (tuple, optional): Background color as an RGB tuple (default is white - (255, 255, 255)).

    Raises:
        ImageProcessingError: If there are any errors during image processing.
    """

    # Open the original image
    try:
        image = Image.open(image_path)
    except (FileNotFoundError, OSError):
        raise ImageProcessingError(f"Invalid image path: {image_path}")

    # Convert the image to RGB mode if it is in RGBA format (PNG file)
    image = image.convert("RGB")

    dpi = image.info.get("dpi")
    # If the DPI value does not exist, set it to (300, 300).
    if dpi is None:
        dpi = (300, 300)
    # Otherwise, check each direction if it is less than 300, and if so, adjust it to 300.
    else:
        dpi = (max(dpi[0], 300), max(dpi[1], 300))

    # Get the size of the original image and the new image
    original_size = image.size
    new_width, new_height = new_size

    # Create a new blank image and fill it with the specified background color
    new_image = Image.new("RGB", new_size, background_color)

    # Calculate the placement position of the original image in the new image to keep it centered
    offset = ((new_width - original_size[0]) // 2, (new_height - original_size[1]) // 2)

    try:
        # Paste the original image onto the center of the new image
        new_image.paste(image, offset)

        # Save the new image
        new_image.save(output_path, dpi=dpi)
    except Exception as e:
        raise ImageProcessingError(f"Error during image processing:  {e}")


# Example usage
def example() -> None:
    try:
        insert_text = "Hello!\nSpace"
        size = 40
        position = (30, 10)

        input_file_path = "./image_sample/astronaut.png"
        output_file_path = change_file_extension(append_text_to_filename(input_file_path, "_mod"), ".jpg")
        # output_file_path = "./image_sample/astronaut_mod.jpg"
        add_text_to_image(input_file_path, output_file_path, insert_text, size, position)

        input_file_path = "./image_sample/lightning.jpg"
        output_file_path = append_text_to_filename(input_file_path, "_mod")
        # output_file_path = "./image_sample/lightning_mod.jpg"
        add_text_to_image(input_file_path, output_file_path, insert_text, size, position)

    except (Exception, ImageProcessingError) as e:
        print(f"Error occurred during image processing: {e}")


def create_ig_story_image(image_path: str, insert_text: str = "") -> None:
    try:
        # Get the size of the original image
        width, height = get_image_size(image_path)

        # Resize image for IG Stories (9:16).
        new_height = int(width * (16 / 9))

        image_width_to_text_ratio = 29
        text_size = round(width / image_width_to_text_ratio)

        image_width_to_text_position_x_ratio = 30.53
        image_height_to_text_position_y_ratio = 7.3
        text_position = (round(width / image_width_to_text_position_x_ratio),
                         round(new_height / image_height_to_text_position_y_ratio))

        output_file_path = append_text_to_filename(image_path, "_ig_story")

        expand_and_center_image(image_path, output_file_path, (width, new_height))

        add_text_to_image(output_file_path, output_file_path, insert_text, text_size, text_position)

    except (Exception, ImageProcessingError) as e:
        print(f"Error occurred during image processing: {e}")


if __name__ == '__main__':
    example()
    create_ig_story_image("./image_sample/lightning.jpg", "Lightning")
