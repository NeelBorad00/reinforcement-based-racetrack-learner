import math
import random
import sys
import os

import neat
import pygame

# Constants
WIDTH = 1869
HEIGHT = 1080

CAR_SIZE_X = 10    
CAR_SIZE_Y = 10

BORDER_COLOR = (255, 255, 255)  # Color To Crash on Hit

current_generation = 0  # Generation counter
fastest_lap_time = float('inf')  # Initialize fastest lap time

# Define lap boundary for tracking lap completion
LAP_START_X = 1196  # X-coordinate to start the lap
LAP_END_X = 50  # X-coordinate to end the lap
LAP_Y_POSITION = 530  # Y-coordinate where the lap is considered finished

class Car:
    def __init__(self):
        # Load Car Sprite and Rotate
        self.sprite = pygame.image.load('car.png').convert()  # Convert speeds up a lot
        self.sprite = pygame.transform.scale(self.sprite, (CAR_SIZE_X, CAR_SIZE_Y))
        self.rotated_sprite = self.sprite 

        self.position = [LAP_START_X, LAP_Y_POSITION]  # Starting position
        self.angle = 0
        self.speed = 0

        self.speed_set = False  # Flag for default speed later on
        self.center = [self.position[0] + CAR_SIZE_X / 2, self.position[1] + CAR_SIZE_Y / 2]  # Calculate center

        self.radars = []  # List for sensors / radars
        self.drawing_radars = []  # Radars to be drawn

        self.alive = True  # Boolean to check if car is crashed
        self.distance = 0  # Distance driven
        self.time = 0  # Time passed
        self.max_speed = 30  # Maximum speed
        self.lap_start_time = None  # Start time for the current lap

    def draw(self, screen):
        screen.blit(self.rotated_sprite, self.position)  # Draw sprite
        self.draw_radar(screen)  # OPTIONAL FOR SENSORS

    def draw_radar(self, screen):
        # Optionally draw all sensors / radars
        for radar in self.radars:
            position = radar[0]
            pygame.draw.line(screen, (0, 255, 0), self.center, position, 1)
            pygame.draw.circle(screen, (0, 255, 0), position, 5)

    def check_collision(self, game_map):
        self.alive = True
        for point in self.corners:
            # If any corner touches border color -> crash
            if game_map.get_at((int(point[0]), int(point[1]))) == BORDER_COLOR:
                self.alive = False
                break

    def check_radar(self, degree, game_map):
        length = 0
        x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
        y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

        # While we don't hit BORDER_COLOR and length < 300 (just a max) -> go further and further
        while not game_map.get_at((x, y)) == BORDER_COLOR and length < 300:
            length += 1
            x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
            y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

        # Calculate distance to border and append to radars list
        dist = int(math.sqrt(math.pow(x - self.center[0], 2) + math.pow(y - self.center[1], 2)))
        self.radars.append([(x, y), dist])
    
    def update(self, game_map):
        # Set the speed to 20 for the first time
        if not self.speed_set:
            self.speed = 20
            self.speed_set = True

        # Get rotated sprite and move into the right X-direction
        self.rotated_sprite = self.rotate_center(self.sprite, self.angle)
        self.position[0] += math.cos(math.radians(360 - self.angle)) * self.speed
        self.position[0] = max(self.position[0], 20)
        self.position[0] = min(self.position[0], WIDTH - 120)

        # Increase distance and time
        self.distance += self.speed
        self.time += 1
        
        # Same for Y-position
        self.position[1] += math.sin(math.radians(360 - self.angle)) * self.speed
        self.position[1] = max(self.position[1], 20)
        self.position[1] = min(self.position[1], HEIGHT - 120)

        # Calculate new center
        self.center = [int(self.position[0]) + CAR_SIZE_X / 2, int(self.position[1]) + CAR_SIZE_Y / 2]

        # Calculate four corners
        length = 0.5 * CAR_SIZE_X
        left_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 30))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 30))) * length]
        right_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 150))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 150))) * length]
        left_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 210))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 210))) * length]
        right_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 330))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 330))) * length]
        self.corners = [left_top, right_top, left_bottom, right_bottom]

        # Check collisions and clear radars
        self.check_collision(game_map)
        self.radars.clear()

        # From -90 to 120 with step-size 45 check radar
        for d in range(-90, 120, 45):
            self.check_radar(d, game_map)

        # Check for lap completion
        if self.position[0] < LAP_END_X and self.lap_start_time is not None:
            # Lap completed
            lap_time = self.time - self.lap_start_time
            self.time = 0  # Reset time for the next lap
            self.lap_start_time = None  # Reset lap start time
            return lap_time  # Return the lap time for tracking

        # Start timing the lap if the car is at the start position
        if self.position[0] > LAP_START_X and self.lap_start_time is None:
            self.lap_start_time = self.time

        return 0  # No lap completed

    def get_data(self):
        # Get distances to border
        radars = self.radars
        return_values = [0, 0, 0, 0, 0]
        for i, radar in enumerate(radars):
            return_values[i] = int(radar[1] / 30)

        return return_values

    def is_alive(self):
        # Basic alive function
        return self.alive

    def get_reward(self):
        # Improved reward function
        if not self.alive:
            return -100  # Penalty for crashing
        return self.distance / (CAR_SIZE_X / 2) + 1  # Reward for distance + small constant to encourage movement

    def rotate_center(self, image, angle):
        # Rotate the rectangle
        rectangle = image.get_rect()
        rotated_image = pygame.transform.rotate(image, angle)
        rotated_rectangle = rectangle.copy()
        rotated_rectangle.center = rotated_image.get_rect().center
        rotated_image = rotated_image.subsurface(rotated_rectangle).copy()
        return rotated_image


def run_simulation(genomes, config):
    
    global fastest_lap_time  # Reference to the global fastest lap time

    # Empty collections for nets and cars
    nets = []
    cars = []

    # Initialize PyGame and the display
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)

    # For all genomes passed, create a new neural network
    for i, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0

        cars.append(Car())

    # Clock settings
    clock = pygame.time.Clock()
    generation_font = pygame.font.SysFont("Arial", 30)
    alive_font = pygame.font.SysFont("Arial", 20)
    lap_time_font = pygame.font.SysFont("Arial", 20)
    game_map = pygame.image.load('map.png').convert()  # Convert speeds up a lot

    global current_generation
    current_generation += 1

    # Simple counter to roughly limit time
    counter = 0

    while True:
        # Exit on quit event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)

        # For each car get the action it takes
        for i, car in enumerate(cars):
            output = nets[i].activate(car.get_data())
            choice = output.index(max(output))
            if choice == 0:
                car.angle += 10  # Left
            elif choice == 1:
                car.angle -= 10  # Right
            elif choice == 2:
                if car.speed > 12:
                    car.speed -= 2  # Slow down
            else:
                if car.speed < car.max_speed:
                    car.speed += 2  # Speed up
        
        # Check if car is still alive
        still_alive = 0
        for i, car in enumerate(cars):
            if car.is_alive():
                still_alive += 1
                lap_time = car.update(game_map)
                genomes[i][1].fitness += car.get_reward()

                # Update fastest lap time if current lap is the fastest
                if lap_time > 0 and lap_time < fastest_lap_time:
                    fastest_lap_time = lap_time

        if still_alive == 0:
            break

        counter += 1
        if counter == 30 * 40:  # Stop after about 20 seconds
            break

        # Draw map and all cars that are alive
        screen.blit(game_map, (0, 0))
        for car in cars:
            if car.is_alive():
                car.draw(screen)
        
        # Display info
        text = generation_font.render("Generation: " + str(current_generation), True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.topright = (WIDTH - 20, 20)  # Position at top right corner with padding
        screen.blit(text, text_rect)

        text = alive_font.render("Still Alive: " + str(still_alive), True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.topright = (WIDTH - 20, 50)  # Position just below the generation text
        screen.blit(text, text_rect)

        lap_time_text = lap_time_font.render("Fastest Lap Time: {:.2f}s".format(fastest_lap_time), True, (0, 0, 0))
        lap_time_rect = lap_time_text.get_rect()
        lap_time_rect.topright = (WIDTH - 20, 80)  # Position just below the alive text
        screen.blit(lap_time_text, lap_time_rect)

        pygame.display.flip()
        clock.tick(60)  # 60 FPS

if __name__ == "__main__":
    
    # Load config
    config_path = "./config.txt"
    config = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation,
                                config_path)

    # Create population and add reporters
    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)
    
    # Run simulation for a maximum of 1000 generations
    population.run(run_simulation, 1000)
