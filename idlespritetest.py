import pygame
import math
import subprocess
import multiprocessing

# Helper function to wrap input text
def wrap_input_text(text, font, max_width):
    """Function to wrap user input to fit within the display width."""
    words = text.split(' ')
    wrapped_lines = []
    current_line = ""

    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            wrapped_lines.append(current_line)
            current_line = word + " "

    wrapped_lines.append(current_line)  # Append the last line
    return wrapped_lines

# Input window with text wrapping
def input_window(response_queue):
    pygame.init()

    screen = pygame.display.set_mode((1, 1), pygame.HIDDEN)  # Temporary small display to allow loading images


    # Load sprite animation frames
    idle_frames = []
    for i in range(4):  # Assuming 4 frames
        try:
            frame = pygame.image.load(f'Gabumon-{i}.png').convert_alpha()
            idle_frames.append(frame)
        except pygame.error as e:
            print(f"Error loading image Gabumon-{i}.png: {e}")
            break

    # Check if frames loaded correctly
    if len(idle_frames) == 0:
        print("No sprite frames loaded. Exiting.")
        pygame.quit()
        exit()

    # Get the dimensions of the first sprite frame
    sprite_width, sprite_height = idle_frames[0].get_size()
    input_box_height = 40  # Give more height to the input area
    display_width = sprite_width + 60
    display_height = sprite_height + input_box_height + 20

    # Set up display size for input window
    screen = pygame.display.set_mode((display_width, display_height), pygame.SRCALPHA)
    clock = pygame.time.Clock()

    font = pygame.font.Font(None, 20)  # Font size 24
    user_input = ""
    frame_index = 0

    # Main loop for input window
    running = True
    while running:
        screen.fill((0, 0, 0, 0))  # Transparent background

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # Send the user input to LLaMA and get a response
                    if user_input.strip():
                        get_llama_response(user_input, response_queue)
                        user_input = ""  # Clear input after sending
                elif event.key == pygame.K_BACKSPACE:
                    user_input = user_input[:-1]  # Remove last character on backspace
                else:
                    user_input += event.unicode  # Add character to input

        # Update sprite animation
        idle_y = 5 * math.sin(pygame.time.get_ticks() / 500)
        frame_index = (frame_index + 0.1) % len(idle_frames)  # Animation update
        current_frame = idle_frames[int(frame_index)]
        center_x = (screen.get_width() - sprite_width) // 2
        screen.blit(current_frame, (center_x, int(idle_y)))

        # Wrap the user input text to fit the display width
        wrapped_input_lines = wrap_input_text(user_input, font, display_width - 20)
        y_offset = sprite_height + 20  # Start rendering below the sprite

        # Render each wrapped line of user input
        for line in wrapped_input_lines:
            input_surface = font.render(line, True, (255, 255, 255))
            screen.blit(input_surface, (10, y_offset))
            y_offset += 20  # Move down for each line

        # Update display
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


# The output window and rest of the code remains the same
def output_window(response_queue):
    pygame.init()

    # Set up display size for output window
    screen = pygame.display.set_mode((500, 300), pygame.RESIZABLE)
    clock = pygame.time.Clock()

    font = pygame.font.Font(None, 24)  # Font size 24
    running = True
    response_text = ""
    y_offset = 20  # Start Y-offset for text
    scroll_speed = 10  # Speed at which text scrolls

    while running:
        screen.fill((0, 0, 0))  # Black background

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    y_offset += scroll_speed  # Scroll up
                elif event.key == pygame.K_DOWN:
                    y_offset -= scroll_speed  # Scroll down

            elif event.type == pygame.MOUSEWHEEL:
                y_offset += event.y * scroll_speed  # Scroll with mouse wheel

        # Check if there's a new response in the queue
        if not response_queue.empty():
            response_text = response_queue.get()

        # Clean the text before displaying to remove special characters
        response_text = clean_text(response_text)

        # Render response text with paragraph indentation and scrolling
        response_lines = wrap_text(response_text, font, 480)
        current_y = y_offset  # Track the current Y position of the text
        for i, line in enumerate(response_lines):
            # Apply indentation to the first line of each paragraph
            if i == 0 or response_lines[i - 1].endswith('.'):
                line_surface = font.render(line, True, (255, 255, 255))
                screen.blit(line_surface, (30, current_y))  # Indent by 30 pixels
            else:
                line_surface = font.render(line, True, (255, 255, 255))
                screen.blit(line_surface, (10, current_y))  # Normal indent for subsequent lines
            current_y += 30  # Move down for each line

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


def wrap_text(text, font, max_width):
    """Function to wrap text to fit within a max width, with paragraph indent."""
    words = text.split(' ')
    wrapped_lines = []
    current_line = ""

    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            wrapped_lines.append(current_line)
            current_line = word + " "

    wrapped_lines.append(current_line)
    return wrapped_lines


def clean_text(text):
    """Function to remove special characters from the text."""
    return text.replace('\n', ' ').replace('\r', ' ').strip()


def get_llama_response(prompt, response_queue):
    """Get the response from LLaMA and send it to the output window."""
    try:
        result = subprocess.run(["ollama", "run", "llama3.2", prompt], capture_output=True, text=True)
        response_queue.put(result.stdout.strip())
    except Exception as e:
        response_queue.put(f"Error: {e}")


def main():
    # Queue to send the LLaMA response from the input window to the output window
    response_queue = multiprocessing.Queue()

    # Create processes for input and output windows
    input_process = multiprocessing.Process(target=input_window, args=(response_queue,))
    output_process = multiprocessing.Process(target=output_window, args=(response_queue,))

    # Start both windows concurrently
    input_process.start()
    output_process.start()

    # Wait for both windows to finish
    input_process.join()
    output_process.join()


if __name__ == '__main__':
    main()
