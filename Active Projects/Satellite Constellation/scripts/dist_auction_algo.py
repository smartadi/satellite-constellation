import numpy as np 
import matplotlib.pyplot as plt
import networkx as nx
from methods import rand_connected_graph, plot_graph
import networkx as nx
from threading import Thread
import time
import scipy.optimize
import random

class Auction(object):
    def __init__(self, n_agents, n_tasks, benefits=None, graph=None):
        if benefits is not None:
            self.benefits = benefits
        else:
            self.benefits = np.random.rand(n_agents, n_tasks)

        if graph != None:
            self.graph = graph
        else:
            self.graph = rand_connected_graph(n_agents)

        self.n_agents = n_agents
        self.n_tasks = n_tasks

        #Initialize agents with ID, benefits and neighbors
        self.agents = [AuctionAgent(self, i, self.benefits[i,:], list(self.graph.neighbors(i))) for i in range(n_agents)]

    def show_graph(self):
        plot_graph(self.graph)

    def solve_centralized(self):
        """
        Doesn't work yet
        """
        row_ind, col_ind = scipy.optimize.linear_sum_assignment(self.benefits, maximize=True)
        print("Centralized solution")
        for row, col in zip(row_ind, col_ind):
            print(f"Agent {row} chose task {col_ind[row]} with benefit {self.benefits[row, col]}")
        print(f"Total benefit: {self.benefits[row_ind, col_ind].sum()}")

    def run_auction(self):
        threads = []
        for i in range(self.n_agents):
            t = Thread(target=AuctionAgent.run_agent_auction, args=(self.agents[i],))
            t.start()
            threads.append(t)

        while sum([agent.agent_prices_stable for agent in self.agents]) < self.n_agents:
            time.sleep(0.1)
        
        for i in range(self.n_agents):
            self.agents[i].continue_auction = False

        for t in threads:
            t.join()

        print("Auction results:")
        for agent in self.agents:
            print(f"Agent {agent.id} chose task {agent.choice} with benefit {agent.benefits[agent.choice]} and price {agent.public_prices[agent.choice]}")
        print(f"Total benefit: {sum([agent.benefits[agent.choice] for agent in self.agents])}")

class AuctionAgent(object):
    def __init__(self, auction, id, benefits, neighbors):
        self.auction = auction
        self.id = id
        self.benefits = benefits

        self.neighbors = neighbors
        self.choice = np.argmax(benefits)

        #Random amount of time to wait
        #self.dt = np.random.randint(1,10)
        self.dt = np.random.rand()

        self.eps = 0.01

        self.public_prices = np.zeros_like(benefits)

        self.public_high_bidders = np.zeros_like(benefits)

        self.agent_prices_stable = False
        self.continue_auction = True
    
    def __repr__(self):
        ret_str = f"Agent {self.id}, neighbors {self.neighbors}\n"
        ret_str += f"\tCurrent prices: {self.public_prices}"
        ret_str += f"\tCurrent high bidders: {self.public_high_bidders}"
        ret_str += f"\tCurrent choice: {self.choice}"
        return ret_str
    
    def run_agent_auction(self):
        
        while self.continue_auction:
            old_prices = self.public_prices
            old_high_bidders = self.public_high_bidders

            neighbor_prices = np.array(self.public_prices)
            highest_bidders = np.array(self.public_high_bidders)
            for n in self.neighbors:
                neighbor_prices = np.vstack((neighbor_prices, self.auction.agents[n].public_prices))
                highest_bidders = np.vstack((highest_bidders, self.auction.agents[n].public_high_bidders))

            max_prices = np.max(neighbor_prices, axis=0)

            # Filter the high bidders by the ones that have the max price, and set the rest to -1.
            # Grab the highest index max bidder to break ties.
            max_price_bidders = np.where(neighbor_prices == max_prices, highest_bidders, -1)
            self.public_high_bidders = np.max(max_price_bidders, axis=0)

            if max_prices[self.choice] >= self.public_prices[self.choice] and self.public_high_bidders[self.choice] != self.id:
                best_net_value = np.max(self.benefits - max_prices)
                second_best_net_value = np.partition(self.benefits - max_prices, -2)[-2] #https://stackoverflow.com/questions/33181350/quickest-way-to-find-the-nth-largest-value-in-a-numpy-matrix

                self.choice = np.argmax(self.benefits-max_prices) #choose the task with the highest benefit to the agent
                
                self.public_high_bidders[self.choice] = self.id
                
                inc = best_net_value - second_best_net_value + self.eps

                self.public_prices = max_prices
                self.public_prices[self.choice] = max_prices[self.choice] + inc
            else:
                #Otherwise, don't change anything and just change your broacast prices
                #based on the new info from other agents.
                self.public_prices = max_prices

            if np.array_equal(self.public_prices, old_prices) and np.array_equal(self.public_high_bidders, old_high_bidders):
                self.agent_prices_stable = True
            else:
                self.agent_prices_stable = False
            time.sleep(self.dt)

# if __name__ == "__main__":
#     #Benefit array which can show proof of suboptimality by epsilon
#     b = np.array([[0.58171674, 0.16394833, 0.9471958,  0.67933512, 0.75647097, 0.96396759],
#                     [0.19934895, 0.89260454, 0.18748017, 0.96584496, 0.37879552, 0.20749475],
#                     [0.07692341, 0.15046442, 0.34058061, 0.93558144, 0.785595,   0.30242082],
#                     [0.53182682, 0.92819657, 0.79620561, 0.71194428, 0.8427648,  0.11332127]])
    
#     a = Auction(4,6, benefits=b)
#     print("Benefits:")
#     print(a.benefits)

#     a.run_auction()
#     a.solve_centralized()





num_agents = 5
num_tasks = 7
G = rand_connected_graph(num_agents)
beta = np.random.rand(num_agents, num_tasks)
p = np.zeros((num_agents, num_tasks))
alpha = np.arange(0, num_agents, 1).astype('int')
b = np.zeros((num_agents, num_tasks)).astype('int')
epsilon = .0001
next_p = np.zeros((num_agents, num_tasks))
next_b = np.zeros((num_agents, num_tasks)).astype('int')
next_alpha = np.zeros(num_agents)


def solve_centralized(beta):
    row_ind, col_ind = scipy.optimize.linear_sum_assignment(beta, maximize=True)
    print("centeralized:", col_ind)
    out = 0
    for i in row_ind:
        out += beta[i,col_ind[i]]
    return out



tol = 1e-5
cost = []
for t in range(100):
    
    total_assignment_benefit = 0
    for i in range(num_agents):
        total_assignment_benefit += beta[i, alpha[i]]
    cost.append(total_assignment_benefit)
    print(t,alpha,total_assignment_benefit)  
    for i in range(num_agents):
        N_i = list(G.neighbors(i))
        N_i.append(i)
        for j in range(num_tasks):
            # update prices
            next_p[i,j] = np.max(p[N_i, j])

            # update highest bidders
            max_value = next_p[i,j]
            max_indices = np.argwhere(abs(max_value - p[N_i,j]) < tol)[:,0]
            next_b[i,j] = np.max(b[max_indices, j])
            next_b = next_b.astype('int')

        if p[i, alpha[i]] <= next_p[i, alpha[i]] and next_b[i, alpha[i]] != i:
            max_value = np.max(beta[i,:] - next_p[i,:])
            L = np.argwhere(abs(max_value - (beta[i,:] - next_p[i,:])) < tol)
            random.shuffle(L)
            next_alpha[i] = L[0]
            next_alpha = next_alpha.astype('int')
            next_b[i, next_alpha[i]] = i
            L = list(beta[i,:] - p[i,:])
            L.sort()
            v_i = L[-1]
            w_i = L[-2]
            gamma_i = v_i - w_i + epsilon
            next_p[i, next_alpha[i]] = p[i, next_alpha[i]] + gamma_i
        else:
            next_alpha[i] = int(alpha[i])
    p = next_p
    b = next_b.astype('int')
    alpha = next_alpha.astype('int')
out = solve_centralized(beta)
print(out)
plt.plot(cost)
plt.grid()
plt.show()
