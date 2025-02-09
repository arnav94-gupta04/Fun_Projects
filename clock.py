import turtle
import datetime
import time

# Configuration parameters for scalability
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
CLOCK_RADIUS = 250
HOUR_HAND_LENGTH = 100
MINUTE_HAND_LENGTH = 150
SECOND_HAND_LENGTH = 200
BACKGROUND_COLOR = "black"
CLOCK_COLOR = "white"

# Set up the screen
screen = turtle.Screen()
screen.title("Arnav Gupta")
screen.bgcolor(BACKGROUND_COLOR)
screen.setup(width=SCREEN_WIDTH, height=SCREEN_HEIGHT)

# Create a shared turtle instance for drawing
clock_turtle = turtle.Turtle()
clock_turtle.hideturtle()
clock_turtle.speed(0)

# Function to draw the static clock face
def draw_clock_face(t, radius):
    """
    Draws the static clock face with hour ticks.
    Args:
        t (turtle.Turtle): The turtle instance used for drawing.
        radius (int): The radius of the clock face.
    """
    t.color(CLOCK_COLOR)
    t.penup()
    t.goto(0, -radius)
    t.pendown()
    t.pensize(2)
    t.circle(radius)

    # Draw hour ticks
    for i in range(12):
        t.penup()
        t.goto(0, 0)
        t.setheading(90 - i * 30)
        t.forward(radius - 20)
        t.pendown()
        t.forward(10)
        t.penup()

# Function to draw a numeric hand
def draw_hand(t, length, angle, color, label):
    """
    Draws a single hand on the clock.
    Args:
        t (turtle.Turtle): The turtle instance used for drawing.
        length (int): Length of the hand.
        angle (float): Angle of rotation for the hand.
        color (str): Color of the hand.
        label (str/int): Label to display at the tip of the hand.
    """
    t.penup()
    t.goto(0, 0)
    t.color(color)
    t.setheading(90 - angle)
    t.forward(length - 20)
    t.write(label, align="center", font=("Courier", 12, "bold"))

# Function to update the clock hands dynamically
def update_clock():
    """
    Updates the clock hands dynamically to reflect the current time.
    """
    hand_turtle = turtle.Turtle()
    hand_turtle.hideturtle()
    hand_turtle.speed(0)

    while True:
        try:
            hand_turtle.clear()
            now = datetime.datetime.now()
            hour = now.hour 
            minute = now.minute
            second = now.second

            # Calculate angles
            hour_angle = (hour + minute / 60) * 30  # Each hour is 30 degrees
            minute_angle = minute * 6               # Each minute is 6 degrees
            second_angle = second * 6               # Each second is 6 degrees

            # Draw hands
            draw_hand(hand_turtle, HOUR_HAND_LENGTH, hour_angle, "cyan", hour if hour != 0 else 12)  # Hour hand
            draw_hand(hand_turtle, MINUTE_HAND_LENGTH, minute_angle, "blue", minute)                # Minute hand
            draw_hand(hand_turtle, SECOND_HAND_LENGTH, second_angle, "red", second)                 # Second hand

            screen.update()
            time.sleep(1)
        except Exception as e:
            print(f"Error while updating clock: {e}")
            break

# Main program
def main():
    """
    Main function to initialize and run the clock program.
    """
    try:
        screen.tracer(0)
        draw_clock_face(clock_turtle, CLOCK_RADIUS)
        update_clock()
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        turtle.done()

if __name__ == "__main__":
    main()
