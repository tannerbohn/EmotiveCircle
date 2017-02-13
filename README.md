# EmotiveCircle
An attempt at creating a pet program.

![EmotiveCircle](https://raw.githubusercontent.com/tannerbohn/tannerbohn.github.io/master/assets/emotive_circle_1.png)

See [post](http://tannerbohn.github.io/2017/02/13/EmotiveCircle/) for more info on project.

## Usage
To run the code, `python main.py`

Inside main.py, you can see the 'directory' value to set. This should be the path to the code.

Inside EmotiveCircle.py, you can see the following important values which can be set:
* `bg_colour`: colour of living cells
* `c1_colour`: colour of center circle
* `c2_colour`: colour of the heartbeat circle (also has opacity value)
* `ball_colour`: colour of the ball
* `dt`: the time step size


When using the program, the following operations are available:
* left-click on left edge of screen: show/hide info
* left-click inside circle: feed
* move cursor over top or bottom of circle: comfort/pet
* move cursor over left or right of circle: poke/annot
* tab: clear goal points
* right click: add goal point to sequence

## Tips
* the pet will only play with the ball when hunger is below a certain threshold