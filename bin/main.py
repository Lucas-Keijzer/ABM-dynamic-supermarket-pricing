import numpy as np

NUMBER_OF_CONSUMERS = 3
NUMBER_OF_DAYS_SIMULATED = 10

class SupermarketAgent:
    def __init__(self, name, average_sales_price, strategy = None):
        self.name = name
        self.average_sales_price = average_sales_price
        self.had_sales_today = False
        self.strategy = strategy
        self.customers_today = 0
        self.customers_yesterday = 0

    def adjust_price(self):
        if not self.had_sales_today:
            self.average_sales_price = double(max(1, self.average_sales_price - 0.1))
            print(f'the new average sales price of {self.name} is: {self.average_sales_price}')
        elif self.had_sales_today:
                self.average_sales_price += double(np.random.uniform(0.1, 0.5))
                self.average_sales_price = double(self.average_sales_price)
                print(f'The new average sales price of {self.name} is: {self.average_sales_price}')
        # else:
        #     print("test")

    def update_customers(self):
        self.customers_yesterday = self.customers_today
        self.customers_today = 0

class ConsumerAgent:
    def __init__(self, name, budget, income, loyalty):
        self.name = name
        self.budget = budget
        self.income = income
        self.loyalty = loyalty

    def update_budget(self):
        self.budget += self.income

def main():
    supermarkets = [
        SupermarketAgent("supermarket A", 5),
        SupermarketAgent("supermarket B", 6),
    ]

    consumers = [
        ConsumerAgent(f"consumer {i+1}", np.random.randint(100, 200), np.random.randint(80, 150), {"supermarket A": random_loyalty(), "supermarket B": random_loyalty()})
        for i in range(NUMBER_OF_CONSUMERS)
    ]

    # Simuleer elke dag
    for day in range(NUMBER_OF_DAYS_SIMULATED):
        print(f'dag {day}')
        
        for supermarket in supermarkets:
            supermarket.had_sales_today = False
        
        for consumer in consumers:
            consumer.update_budget()
            
            # fast restriction for 50% change of making a purchase
            if np.random.random() > 0.5:
                continue

            # Find the best score
            beste_score = float('-inf')
            gekozen_supermarket = None
            
            for supermarket in supermarkets:
                totale_score = consumer.loyalty[supermarket.name] / supermarket.average_sales_price
                
                if totale_score > beste_score:
                    beste_score = totale_score
                    gekozen_supermarket = supermarket
            
            kosten = gekozen_supermarket.average_sales_price
            consumer.budget -= kosten
            consumer.budget = double(consumer.budget)
            gekozen_supermarket.had_sales_today = True
            gekozen_supermarket.customers_today += 1

            print(f"{consumer.name} koopt bij {gekozen_supermarket.name} voor {kosten} (nieuw budget: {consumer.budget})")

        for supermarket in supermarkets:
            supermarket.adjust_price()

def random_loyalty():
    return np.random.uniform(low=0, high=0.5)

def double(input):
    return int(input*100) / 100

if __name__ == "__main__":
    main()
