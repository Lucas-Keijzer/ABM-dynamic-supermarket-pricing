import numpy as np
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
import matplotlib.pyplot as plt

NUMBER_OF_CONSUMERS = 3
NUMBER_OF_DAYS_SIMULATED = 10

CONSUMER_INCOME = 0
CONSUMER_INITIAL = np.random.randint(100, 200)

def double(input):
    return int(input * 100) / 100

class SupermarketAgent(Agent):
    def __init__(self, unique_id, model, name, average_sales_price, initial_budget):
        super().__init__(unique_id, model)
        self.name = name
        self.average_sales_price = average_sales_price
        self.budget = initial_budget
        self.had_sales_today = False
        self.customers_today = 0
        self.customers_yesterday = 0
        self.experience_score = np.random.uniform(0.5, 1.0)  

    def adjust_price(self):
        if not self.had_sales_today:
            self.average_sales_price = double(max(1, self.average_sales_price - 0.1))
            print(f'The new average sales price of {self.name} is: {self.average_sales_price}')
        else:
            self.average_sales_price += double(np.random.uniform(0.1, 0.5))
            self.average_sales_price = double(self.average_sales_price)
            print(f'The new average sales price of {self.name} is: {self.average_sales_price}')

    def update_customers(self):
        self.customers_yesterday = self.customers_today
        self.customers_today = 0
        self.had_sales_today = False

    def update_budget(self):
        sales_revenue = self.customers_yesterday * self.average_sales_price
        self.budget += sales_revenue
        print(f'{self.name} budget after day {self.model.current_day}: {self.budget}')

    def update_experience(self):
        if self.had_sales_today:
            self.experience_score = double(min(1.0, self.experience_score + 0.01))
        else:
            self.experience_score = double(max(0.5, self.experience_score - 0.01))
        print(f'{self.name} experience score after day {self.model.current_day}: {self.experience_score}')

    def step(self):
        self.update_budget()
        self.adjust_price()
        self.update_experience()
        self.update_customers()

class ConsumerAgent(Agent):
    def __init__(self, unique_id, model, name, budget, income, loyalty):
        super().__init__(unique_id, model)
        self.name = name
        self.budget = budget
        self.income = income
        self.loyalty = loyalty

    def update_budget(self):
        self.budget += self.income

    def increase_loyalty(self, supermarket_name):
        self.loyalty[supermarket_name] += 0.05
        self.loyalty[supermarket_name] = double(min(self.loyalty[supermarket_name], 1.0))  
        print(f'{self.name} loyalty to {supermarket_name} increased to: {self.loyalty[supermarket_name]}')

    def step(self):
        self.update_budget()

        if np.random.random() > 0.5:
            return

        best_score = float('-inf')
        chosen_supermarket = None

        for supermarket in self.model.supermarkets:
            total_score = (self.loyalty[supermarket.name] * supermarket.experience_score) / supermarket.average_sales_price
            if total_score > best_score:
                best_score = total_score
                chosen_supermarket = supermarket

        if chosen_supermarket:
            cost = chosen_supermarket.average_sales_price
            if self.budget - cost < 0:
                return
            self.budget -= cost    
            self.budget = double(self.budget)
            chosen_supermarket.had_sales_today = True
            chosen_supermarket.customers_today += 1
            self.increase_loyalty(chosen_supermarket.name)

class SupermarketModel(Model):
    def __init__(self, num_consumers, num_days):
        super().__init__()
        self.num_consumers = num_consumers
        self.num_days = num_days
        self.current_day = 0
        self.running = True
        self.schedule = RandomActivation(self)
        
        # Create Supermarkets 
        self.supermarkets = [
            SupermarketAgent(1, self, "supermarket A", 5, 1000),
            SupermarketAgent(2, self, "supermarket B", 6, 1000),
        ]
        for supermarket in self.supermarkets:
            self.schedule.add(supermarket)

        # Create Consumers
        for i in range(self.num_consumers):
            loyalty = {supermarket.name: self.random_loyalty() for supermarket in self.supermarkets}
            consumer = ConsumerAgent(i + 3, self, f"consumer {i+1}", CONSUMER_INITIAL, CONSUMER_INCOME, loyalty)
            self.schedule.add(consumer)
        
        self.datacollector = DataCollector(
            agent_reporters={"Budget": "budget"},
            model_reporters={
                "Supermarket A Price": lambda m: m.supermarkets[0].average_sales_price,
                "Supermarket B Price": lambda m: m.supermarkets[1].average_sales_price
            }
        )

    def random_loyalty(self):
        return np.random.uniform(low=0, high=0.5)

    def step(self):
        print(f"Day {self.current_day + 1}")
        self.datacollector.collect(self)
        self.schedule.step()
        self.current_day += 1
        if self.current_day >= self.num_days:
            self.running = False

model = SupermarketModel(NUMBER_OF_CONSUMERS, NUMBER_OF_DAYS_SIMULATED)
while model.running:
    model.step()

for agent in model.schedule.agents:
    if isinstance(agent, ConsumerAgent):
        print(f'{agent.name} final budget: {agent.budget}')
# for supermarket in model.supermarkets:
#     print(f'{supermarket.name} final budget: {supermarket.budget}, final experience score: {supermarket.experience_score}')

data = model.datacollector.get_model_vars_dataframe()
data.plot()
plt.title('Supermarket Sales Prices Over Time')
plt.xlabel('Day')
plt.ylabel('Average Sales Price')
plt.show()
