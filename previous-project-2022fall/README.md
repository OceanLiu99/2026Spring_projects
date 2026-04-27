# 2022Fall_projects
![Image text](https://github.com/PhiloJiaqiWang/2022Fall_projects/blob/main/img/img1.jpg)
## Game Background
Stardew Valley is an open-ended country-life RPG! You’ve inherited your grandfather’s old farm plot in Stardew Valley. There is one part in this game that you can take adventures under the mines. There are 120 floors (sometimes called levels) in the Mines. Ore type and quantity increases as The Player moves deeper into the Mines.  
The Mines are filled with rocks and dirt patches. Rocks can be mined with a Pickaxe in order to obtain Stone, ore and Geodes. To advance deeper in the Mines, a ladder must be revealed on each floor. The ladder will appear after breaking rocks or after defeating an enemy (killing enemies is the stamina-free option to finding ladders). 
All the data and probability are listed on the [Stardew Valley Wiki](https://stardewvalleywiki.com/Stardew_Valley_Wiki).
## The Mines
Elements
- Floor  
There are 120 floors in total, the map is drawn randomly with different types, and there are random rocks scattered in the floor.
To get to the next floor, you need to find the ladder which is hid under a random rock.
There is an elevator to get you to 10, 20, 30…, those floors have treasure chest with different items
- Rocks  
Rocks are randomly scattered in the floor. You need a pickaxe to crack the rock. Stone, ore and Geodes will be gained with a set probability. The probability is listed on the Stardew Valley Wiki. The geodes require extra step to be cracked again (money cost) to gain actual items.
There is one rock under which is the ladder
- Equipment  
The player can equip a weapon, a pair of footwear and two rings, which affects the attacking attributes.
- Skill level  
There are five different skills in the game, but only the mining skills is considered in out simulation.
There are 10 levels in total, when achieving level 5, you can choose different occupation, and each will lead to different rewards in the next 5 levels.
- Monster  
There will be monsters in each floor. The types of monsters vary through the depth of the floor, and different monsters have unique traits. After killing a monster, items will be dropped.
- Attack  
Attack happens between the player and the monsters.
The attributes include : Attack, Crit. Chance, Crit. Power, Defense, Immunity, Luck, Magnetism, Speed, Weight
- Health bar and Energy bar  
The attack from the monsters affects the health bar, the using of pickaxe and player attacking affects the energy bar
- Prerequisites for using Monte Carlo  
1. Rerun and Independence: We consider the exhaustion of either health bar or energy bar as the end of one day. So, tomorrow is another day!!!
2. summary of aggregate statistics:  
we compare the total values of gained items in this one-day mining. Since it generates a whole bunch of data, we will draw it using pandas to see the trends (if convergent, we guess it might be a normal distribute). Simply using the mean value and the variance could also be the metrics.
3. Experiments and predictions  
We will use it to verify our hypothesis
## Hypothesis
1. When equipped with the infinity dagger, it is more rewarding to start from 80th floor than from 1st  floor.
2. The ruby ring is more useful than the jade ring when equipped with Burglar's Shank and starts from 1st floor.
3. When reaching level 5 of mining skills, it is more rewarding to choose miner than geologist.
## Classes
- Equipment  
```python  
class Equipment:  

    def __init__(self, name):
        self.name = name
        ep = pd.read_csv('equipments_db.txt', sep=',')
        if name in ep['name'].values:
            self.damage_min = ep[ep.name == name]['damage_min'].values[0]
            self.damage_max = ep[ep.name == name]['damage_max'].values[0]
            self.base_crit_chance = ep[ep.name == name]['base_crit_chance'].values[0]
            self.crit_chance = ep[ep.name == name]['crit_chance'].values[0]
            self.crit_power = ep[ep.name == name]['crit_power'].values[0]
            self.defense = ep[ep.name == name]['defense'].values[0]
            self.immunity = ep[ep.name == name]['immunity'].values[0]
            self.luck = ep[ep.name == name]['luck'].values[0]
        else:
            self.damage_min = 0
            self.damage_max = 0
            self.base_crit_chance = 0
            self.crit_chance = 0
            self.crit_power = 0
            self.defense = 0
            self.immunity = 0
            self.luck = 0
```
- Player  
```python
class Player:
    player_skill_level = 0  # mining skill level
    player_equipments = []  # the list of equipments [weapon, footwear, ring_one, ring_two]
    player_att = []  # the list of attributes
    # [id,name,level,damage_min,damage_max,base_crit_chance,crit_chance,crit_power,defense,immunity,luck]
    player_health_energy = [100, 270]  # [health bar, energy bar]
    player_profession = []
```
- Rock  
```python
class Rock:

    # read the rock spreadsheet
    def __init__(self):
        """
        read rock items and possibility table into the program
        """
        self.r = pd.read_csv('rock.csv')
        self.r.set_index("item", inplace=True)
```
- Monster  
```python
class Monster(object):

    killable, HP, damage, defense, speed, XP, drop_rate = True, 0, 0, 0, 0, 0, {}
```
- Floor  
```python
class Floor:

    def __init__(self, level):
        self.r = pd.read_csv('rock.csv')
        self.r.set_index("item", inplace=True)
        self.level = level
        self.floor_containers = []  # the list of the rocks in this floor
        self.floor_monsters = []  # the list of the monsters
        self.total_value = 0  # total value of all the rocks in this floor
```
- MainGame  
```python
class MainGame:

    total_value = 0
    survive_between = [1, 1]
    if_gameover = False

    def __init__(self, level_start, player: Player, profession):
        """

        :param level_start: the floor the player starts
        :param player: the player
        :param profession: the profession the player chooses, either miner or geologist
        """
        self.survive_between = [level_start, level_start]
        self.this_player = player
        self.profession = profession
        while True:
            if self.if_gameover:
                break
            self.one_floor(level_start)
            level_start = level_start + 1
            self.survive_between[1] = level_start
```
## Variables
- The number of rocks in every floor  
uniformly distributed between [30,50]
- The number of monsters in every floor  
uniformly distributed between [5,10]
- The item in the rock  
see [Stardew Valley Wiki.com-The_Mines-Crates_and_Barrels](https://stardewvalleywiki.com/The_Mines#Crates_and_Barrels)
![Image text](https://github.com/PhiloJiaqiWang/2022Fall_projects/blob/main/img/%E6%88%AA%E5%B1%8F2022-12-10%2010.17.13.png)
- The monster type in every floor  
see [Stardew Valley Wiki.com-Monsters](https://stardewvalleywiki.com/Monsters))
![Image text](https://github.com/PhiloJiaqiWang/2022Fall_projects/blob/main/img/%E6%88%AA%E5%B1%8F2022-12-10%2010.17.52.png)
- The item the monster drops  
- The attack damage  
uniformly distributed between [min_damage, max_damage]
- The chance of critical attack and its power  
## Basic Assumptions
- There is no supplement to fulfill the health bar and energy bar. The exhaustion of either bar means the day ends.
- When fighting with the monsters, the player and the monster take turns to attack each other.
- The value of items are determined by the directly selling value, and the player won’t  process them into more valuable products.
- The player will only enter the next floor after all the monsters are killed and all the items are collected.
- If the game ends, the items the player gained in that level will be proportional to the monsters the player killed.
- The attack damage will conform uniform distribution between min damage and max damage.
- The numbers of rocks in every floor will conform uniform distribution between [30, 50], and monsters between [5,10]
## Validating
- Statistical Convergence  
![Image text](https://github.com/PhiloJiaqiWang/2022Fall_projects/blob/main/hypothesis1-1--1000.png)  
![Image text](https://github.com/PhiloJiaqiWang/2022Fall_projects/blob/main/TotalValue.png)
- Correlation (damage and total value)  
![Image text](https://github.com/PhiloJiaqiWang/2022Fall_projects/blob/main/DamagaAndValue.png)
## Hypothesis 1
`When equipped with the infinity dagger, it is more rewarding to start from 80th floor than from 1st  floor.`  
  
  
The player can choose to start from 1st, 10th, 20th…floor. When the floor is deeper, the rocks will generate more valuable items, 
but the monsters will also advance.  
We simulate the program 1000 times. From the program output, the resulting average total value of starting from 1st floor is 3618
the average total value of starting from 80th is 1068.  
From the histogram, we can see that it is more rewarding to start from 1st  floor than from 80th  floor.  
Thus, this hypothesis is not valid.  
![Image text](https://github.com/PhiloJiaqiWang/2022Fall_projects/blob/main/hypothesis1-80--1000.png)
## Hypothesis 2
`The ruby ring is more useful than the jade ring when equipped with Burglar's Shank and starts from 1st floor.`  
  
  
![Image text](https://github.com/PhiloJiaqiWang/2022Fall_projects/blob/main/img/%E6%88%AA%E5%B1%8F2022-12-05%2023.24.21.png)  
We simulate the program 1000 times. From the program output, the resulting average total value of Ruby Ring is 1275  
the average total value of Jade Ring is 1172  
![Image text](https://github.com/PhiloJiaqiWang/2022Fall_projects/blob/main/hypothesis3-JadeRing--1000.png)  
It is hard to see the result from the picture, and those two results are fairly close.  
Thus we have run it for sevral time. In every time, the total value of Ruby Ring is greater than the Jade Ring.  
We accept the hypothsis.  
## Hypothesis 3
`When reaching level 5 of mining skills, it is more rewarding to choose miner than geologist.`  
  
Method: fixed Parameter: Skill level 5, Player equipped with Sneakers and Infinity Dagger    
Variables: simulation 500 times of two professions, Miner and geologist. We compare the resulting total gold value of two different professions. Finally we choose either the miner or geologist to be the more rewarding profession.  
![Image text](https://github.com/PhiloJiaqiWang/2022Fall_projects/blob/main/img/%E6%88%AA%E5%B1%8F2022-12-10%2010.41.45.png)
We simulate the program 500 times. From the program output, the resulting average total value of Miner is 3593  
the average total value of Geologist is 4262  
From the histogram, we can see that the Geologist profession can produce more values than the Miner  
![Image text](https://github.com/PhiloJiaqiWang/2022Fall_projects/blob/main/hypothesis2-Geologist--500.png)
## Presentation
see Video [here](https://mediaspace.illinois.edu/media/t/1_ikmjbvxq)
