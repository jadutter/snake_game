# ability to limit what the agent sees
# ability to control layers and construction of agent
from keras.optimizers import Adam
from keras.models import Sequential
from keras.layers.core import Dense, Dropout
import random
import numpy as np
import pandas as pd
from operator import add
import copy

NUMBER_OF_INPUTS = 11
class DQN(object):
    """docstring for DQN"""
    __defaults = {
        "weights":{
            "type":  str,
            "value":  "weights.hdf5",
        },
        "learning_rate":{
            "type":  float,
            "value":  0.0005,
        },
        "gamma":{
            "type":  float,
            "value":  0.9,
        },
        "cmd_options":{
            "type":  dict,
            "value":  {
                "0": 0,
                # up, north
                "1": 1,
                # right, east
                "2": 2,
                # down, south
                "3": 3,
                # left, west
                ###############################
                # "4": 4,
                # # escape/spacebar /pause/play
                # "5": 5,
                # restart/start
                # "6": 6,
                # # quit
            },
        },
        ###############
        "epsilon":{
            "type":  int,
            "value":  0,
        },
        "reward":{
            "type":  int,
            "value":  0,
        },
        "dataframe":{
            # pandas DataFrame
            "type":  pd.DataFrame,
            "value":  pd.DataFrame(),
        },
        "short_memory":{
            # numpy array
            "type":  np.array,
            "value":  np.array([]),
        },
        "memory":{
            "type":  list,
            "value":  [],
        },
        ###############

        # "agent_target":{
        #     "type":  int,
        #     "value":  1,
        # },
        # "agent_predict":{
        #     "type":  int,
        #     "value":  0,
        # },
    }
    def __init__(self, *args, **kwargs):
        super(DQN, self).__init__()
        kwargs = {k:v for k,v in kwargs.items() if k in self.__defaults.keys()}
        # remove any unapproved keywords
        for k,v in self.__defaults.items():
            # for each approved keyword argument
            setattr(self, k, kwargs.get(k,v))
            # set the attribute to the value that was given,
            # else use the default value
        # self.reward = 0
        # self.gamma = 0.9
        # self.dataframe = pd.DataFrame()
        # # create pandas DataFrame
        # self.short_memory = np.array([])
        # self.agent_target = 1
        # self.agent_predict = 0
        # self.model = 
        # # create the neurons for this agent
        # #self.model = self.network("weights.hdf5")
        # self.epsilon = 0
        # self.actual = []
        # self.memory = []
        self.epsilon = 0
        self.reward = 0
        self.dataframe = pd.DataFrame()
        self.short_memory = np.array([])
        self.memory = []
        self._memory_limit = 1000
        
    def __del__(self):
        if self.weights and self.model:
            self.model.save_weights(self.weights)

    @property
    def weights(self):
        """
        The 'weights' property is a string representing the path 
        to an hdf5 file.
        """
        return self._weights
    
    @weights.setter
    def weights(self, value):
        self._weights = value

    def save_weights(self):
        """
        Save the current weighted values to the file at 
        self.weights_file
        """
        return self.model.save_weights(self.weights)

    def load_weights(self):
        """
        Read and use the current weighted values in the file at 
        self.weights_file
        """
        return self.model.load_weights(self.weights)

    def init_model(self):
        """
        Create a model property.
        """
        self._model = self.construct_network()

    @property
    def model(self):
        """
        The 'model' property for the DQN.
        """
        if not hasattr(self,"_model"):
            self.init_model()
        return self._model

    def construct_network(self, *args, **kwargs):
        model = Sequential()
        # initialize a sequential model
        model.add(Dense(output_dim=120, activation='relu', input_dim=NUMBER_OF_INPUTS))
        model.add(Dropout(0.15))
        # create a Dense layer using "rectified linear unit" activation 

        model.add(Dense(output_dim=120, activation='relu'))
        model.add(Dropout(0.15))
        # create a Dense layer using "rectified linear unit" activation 
        
        model.add(Dense(output_dim=120, activation='relu'))
        model.add(Dropout(0.15))
        # create a Dense layer using "rectified linear unit" activation 
        
        model.add(Dense(output_dim=3, activation='softmax'))
        # create a Dense layer using Softmax activation function
        
        opt = Adam(self.learning_rate)
        # init an optimizer

        model.compile(loss='mse', optimizer=opt)
        # compile the model using the optimizer, using a mean squared error loss function

        weights = kwargs.get("weights", None)
        if weights:
            # if weights were given
            model.load_weights(weights)
            # load and use the weights in the model
        return model

    #     self._model = local_namespace["model"]
    #     # https://keras.io/models/sequential/


    #     # https://keras.io/layers/core/
    #     # Dense = Just your regular densely-connected NN layer.
    #     # Dropout = Applies Dropout to the input.
        
    #     # https://keras.io/activations/
    #     # activation functions
    #     # None - linear
    #     # relu - Rectified linear unit
    #     # elu - Exponential linear unit.
    #     # softmax - Softmax activation function.
    #     # selu - Scaled Exponential Linear Unit (SELU).
    #     # softplus - Softplus activation function.
    #     # softsign - Softsign activation function.
    #     # tanh - Hyperbolic tangent activation function.
    #     # sigmoid - Sigmoid activation function.
    #     # hard_sigmoid - Hard sigmoid activation function.
    #     # exponential - Exponential (base e) activation function.
    #     # linear - Linear (i.e. identity) activation function.
    #     ###### ADVANCED ######
    #     # LeakyReLU - Leaky version of a Rectified Linear Unit.
    #     # PReLU - Parametric Rectified Linear Unit.
    #     # ThresholdedReLU - Thresholded Rectified Linear Unit.



    def get_state(self, game, player, food):
        # game.game_state = [
        #     [
        #         self.playing,
        #         # whether the game is playing/paused
        #         self.crashed,
        #         # whether the game is playing/quit/crashed
        #         self.score,
        #         # current score for the game
        #         self.size,
        #         # how big a virual pixel is
        #         self.height,
        #         # the height of the playing field for this game
        #         self.width,
        #         # the width of the playing field for this game
        #         self.snake_speed,
        #         # how fast the snake is limited to move
        #         self.auto_tick,
        #         # whether the snake continues to move when playing but in absent of a move command
        #     ],
        #     # the obstacles 
        #     [
        #         seg.dimensions for seg in self.obstacles
        #         # positions of obstacle segments
        #     ],
        #     # the rewards 
        #     [
        #         [seg.dimensions, seg.value] for seg in self.rewards
        #         # [seg.x, seg.y, seg.value] for seg in self.rewards
        #         # positions & values of rewards
        #     ],
        #     # the snake 
        #     [
        #         [ 
        #             [seg.dimensions, seg.heading] for seg in self.snake.segments 
        #             # positions of snake segments
        #         ],
        #         self.snake.belly,
        #         # how many points are in the snakes belly
        #         self.snake.length,
        #         # how long overall the snake is
        #     ],
        # ]
        return game.game_state
    def choose_action(self, state):
        """
        Given the current state of the game, 
        predict the best action to take.
        """
        prediction = self.model.predict(state.reshape((1, NUMBER_OF_INPUTS)))
        return to_categorical(np.argmax(prediction[0]), num_classes=len(self.cmd_options))

    def decide(self, game):
        """
        Observce the current game state, make a decision,
        execute the decision, reevaluate how good the decision was.
        """
        old_state = copy.deepcopy(game.game_state)
        move = self.choose_action(old_state)
        game.next_cmd = move
        while game.next_cmd is not None:
            time.sleep(1)
        new_state = copy.deepcopy(game.game_state)
        self.learn(state_old, new_state, move)
        # self.train_short_memory(state_old, final_move, reward, state_new, game.crash)
        return
    # def learn(self, old_state, new_state, decision):
    #     # playing, crashed, score, size, height, width, snake_speed, auto_tick, obstacles, rewards, snake = *old_state
    #     old_reward = old_state[2]
    #     new_reward = new_state[2]
    #     old = self._reshape_state(old_state)
    #     new = self._reshape_state(new_state)
    #     target = new_reward
    #     if not new_state[1]:
    #         # if the game is still ongoing (not crashed)
    #         prediction = self.model.predict(new)[0]
    #         # generate predictions for how much reward we should gain 
    #         target = new_reward + self.gamma * np.amax(prediction)

    #     target_f = self.model.predict(old)

    #     target_f[0][np.argmax(decision)] = target

    #     self.model.fit(old, target_f, epochs=1, verbose=0)
    def learn(self, old_state, new_state, decision):
        # old_state:
        #     0  playing
        #     1  crashed
        #     2  score
        #     3  size
        #     4  height
        #     5  width
        #     6  snake_speed
        #     7  auto_tick
        #     8  obstacles
        #     9  rewards
        #     10 snake
        old_reward = old_state[2]
        new_reward = new_state[2]
        old = self._reshape_state(old_state)
        new = self._reshape_state(new_state)
        target = new_reward
        if not new_state[1] and not new_state[0]:
            # if the game is still ongoing (not crashed, or paused)
            prediction = self.model.predict(new)[0]
            # Generates output predictions for the input samples
            prediction = np.amax(prediction)
            # the agent should be choosing the one with the best outcome
            target = new_reward + self.gamma * prediction
            # the agent should be choosing the one with the best outcome

        target_f = self.model.predict(old)

        target_f[0][np.argmax(decision)] = target

        self.model.fit(old, target_f, epochs=1, verbose=0)
    
    def _reshape_state(self,state):
        return state.reshape((1, NUMBER_OF_INPUTS))

    def remember(self, old_state, new_state, decision):
        """
        Hold onto the state.
        """
        self.memory.append((old_state, new_state, decision, ))

    def train_from_memory(self, memory):
        if len(memory) > self._memory_limit:
            minibatch = random.sample(memory, self._memory_limit)
        else:
            minibatch = memory


        for index, (old_state, new_state, decision) in enumerate(minibatch):
            old_reward = old_state[2]
            new_reward = new_state[2]
            old = self._reshape_state(old_state)
            new = self._reshape_state(new_state)
            target = new_reward
            # debug(f"done {done}")
            if not new_state[1] and not new_state[0]:
                # if the game is still ongoing (not crashed, or paused)
                prediction = self.model.predict(new)[0]
                # Generates output predictions for the input samples
                prediction = np.amax(prediction)
                # the agent should be choosing the one with the best outcome
                target = new_reward + self.gamma * prediction
                # the agent should be choosing the one with the best outcome

            target_f = self.model.predict(np.array([state]))
            target_f[0][np.argmax(action)] = target
            self.model.fit(np.array([state]), target_f, epochs=1, verbose=0)
    # def train_short_memory(self, state, action, reward, next_state, done):
    #     target = reward
    #     if not done:
    #         target = reward + self.gamma * np.amax(self.model.predict(next_state.reshape((1, 11)))[0])
    #     target_f = self.model.predict(state.reshape((1, 11)))
    #     target_f[0][np.argmax(action)] = target
    #     self.model.fit(state.reshape((1, 11)), target_f, epochs=1, verbose=0)
    #     return








