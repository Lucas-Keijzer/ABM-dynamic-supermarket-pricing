from mesa import Agent
from mesa import Model
from mesa.time import RandomActivation
from mesa.time import BaseScheduler
from mesa.space import ContinuousSpace
import random
import pandas as pd
from PARAMETERS import *


class Supermarket(Agent):
    def __init__(self, unique_id, model, location, experience, price_margin, pricing_strategy='EDLP'):
        super().__init__(unique_id, model)
        self.location = location
        self.experience = experience
        self.price_margin = price_margin
        self.pricing_strategy = pricing_strategy
        self.customers_visited = 0
        self.previous_customers_visited = 0
        self.base_price = 50
        self.total_profit = 0
        self.prices_over_time = []
        self.customers_history = []

    @property
    def average_price(self):
        return self.base_price + self.price_margin

    def adjust_price(self):
        if self.pricing_strategy == 'Dynamic':
            if self.customers_visited > self.previous_customers_visited:
                self.price_margin += price_adjustment
            elif self.customers_visited < self.previous_customers_visited:
                self.price_margin -= price_adjustment

            self.price_margin = max(0 - self.base_price * 0.4, self.price_margin)
            self.price_margin = min(self.base_price * 2, self.price_margin)
        elif self.pricing_strategy == 'random-dynamic':
            fluctuation = random.uniform(-0.5, 0.5)
            self.price_margin = max(0, self.price_margin + fluctuation)

    def step(self):
        self.adjust_price()
        current_price = self.average_price
        self.prices_over_time.append(current_price)
        self.customers_history.append(self.customers_visited)
        self.previous_customers_visited = self.customers_visited
        self.customers_visited = 0


class Customer(Agent):
    def __init__(self, unique_id, model, location):
        super().__init__(unique_id, model)
        self.location = location
        self.loyalty = {supermarket.unique_id: 0 for supermarket in model.supermarkets}
        self.max_loyalty = 100
        self.loyalty_decrement = loyalty_decrement
        self.last_supermarket = None

    def step(self):
        supermarkets = self.model.supermarkets
        chosen_supermarket = min(supermarkets, key=lambda s: self.calculate_utility(s))
        # print("Chosen supermarket", chosen_supermarket)
        if self.last_supermarket is not None and chosen_supermarket.unique_id != self.last_supermarket:
            self.loyalty[self.last_supermarket] = max(0, self.loyalty[self.last_supermarket] - self.loyalty_decrement)

        self.loyalty[chosen_supermarket.unique_id] = min(self.max_loyalty, self.loyalty[chosen_supermarket.unique_id] + loyalty_increase)
        self.last_supermarket = chosen_supermarket.unique_id

        chosen_supermarket.customers_visited += 1
        chosen_supermarket.total_profit += normal_customer_payement + chosen_supermarket.price_margin

    def calculate_utility(self, supermarket):
        distance = self.model.calculate_distance(self.location, supermarket.location)
        price = supermarket.average_price
        experience = supermarket.experience
        loyalty = self.loyalty[supermarket.unique_id]

        utility = (distance_weight * distance +
                   price_weight * price +
                   experience_weight * (1 - experience) +
                   loyalty_weight * (-loyalty))
        # print("consumer", self.unique_id, "utillity:", utility)
        # print(supermarket)
        return utility


class LoyalCustomer(Agent):
    def __init__(self, unique_id, model, location, supermarket):
        super().__init__(unique_id, model)
        self.location = location
        self.supermarket = supermarket

    def step(self):
        self.supermarket.customers_visited += 1
        self.supermarket.total_profit += loyal_customer_payement


class SupermarketModel(Model):
    def __init__(self, N_customers, N_supermarkets, width, height, pricing_strategies):
        self.num_customers = N_customers
        self.num_supermarkets = N_supermarkets
        self.schedule = RandomActivation(self)
        self.space = ContinuousSpace(width, height, torus=False)
        self.supermarkets = []
        self.customers_data = []
        self.profits_data = []
        self.prices_data = []

        # Init supermarkets
        for i in range(self.num_supermarkets):
            
            location = (
                random.uniform(width * supermarket_location_factor, width * (1 - supermarket_location_factor)),
                random.uniform(height * supermarket_location_factor, height * (1 - supermarket_location_factor))
            )
            experience = random.random()
            pricing_strategy = pricing_strategies[i]
            supermarket = Supermarket(i, self, location, experience, price_margin, pricing_strategy)
            self.space.place_agent(supermarket, location)
            self.supermarkets.append(supermarket)
            self.schedule.add(supermarket)

        # Split num loyal/standard customers
        num_loyal_customers = int(self.num_customers * percentage_loyal_customers) 
        num_flexible_customers = self.num_customers - num_loyal_customers

        # Init customers
        for i in range(num_loyal_customers):
            location = (random.uniform(0, width), random.uniform(0, height))
            supermarket = random.choice(self.supermarkets)
            customer = LoyalCustomer(i + self.num_supermarkets, self, location, supermarket)
            self.space.place_agent(customer, location)
            self.schedule.add(customer)

        for i in range(num_flexible_customers):
            location = (random.uniform(0, width), random.uniform(0, height))
            customer = Customer(i + self.num_supermarkets + num_loyal_customers, self, location)
            self.space.place_agent(customer, location)
            self.schedule.add(customer)

    def step(self):
        self.schedule.step()
        self.record_data()

    def record_data(self):
        customer_counts = {f"supermarket_{self.supermarkets[i].pricing_strategy}_{i}": s.customers_history[-1] for i, s in enumerate(self.supermarkets)}
        profits = {f"supermarket_{self.supermarkets[i].pricing_strategy}_{i}": s.total_profit for i, s in enumerate(self.supermarkets)}
        prices = {f"supermarket_{self.supermarkets[i].pricing_strategy}_{i}": s.prices_over_time[-1] for i, s in enumerate(self.supermarkets)}

        self.customers_data.append(customer_counts)
        self.profits_data.append(profits)
        self.prices_data.append(prices)

    def calculate_distance(self, loc1, loc2):
        x1, y1 = loc1
        x2, y2 = loc2
        return ((x1 - x2)**2 + (y1 - y2)**2)**0.5


if __name__ == "__main__":
    placeholder = ['EDLP', 'Dynamic']
    pricing_strategies = [placeholder[x % 2] for x in range(num_supermarkets)]

    all_customers_data = []
    all_profits_data = []
    all_prices_data = []

    for sim in range(num_simulations):
        print(f'Running simulation {sim + 1}/{num_simulations}')

        model = SupermarketModel(num_customers, num_supermarkets, width, height, pricing_strategies)
        for i in range(steps):
            print(f'Simulation {sim + 1}, Day {i + 1}:')
            model.step()

        all_customers_data.extend(model.customers_data)
        all_profits_data.extend(model.profits_data)
        all_prices_data.extend(model.prices_data)

    customers_df = pd.DataFrame(all_customers_data)
    profits_df = pd.DataFrame(all_profits_data)
    prices_df = pd.DataFrame(all_prices_data)

    customers_df.to_csv('customers_over_time.csv', index=False)
    profits_df.to_csv('profits_over_time.csv', index=False)
    prices_df.to_csv('prices_over_time.csv', index=False)

    print("Aggregated data has been saved to CSV files.")
    