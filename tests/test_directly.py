
from pmkoalas.dtlog import convert
from vispm import DirectlyFollowsPresentor
from matplotlib import pyplot as plt

if __name__ == "__main__":

    log = convert(
        "a c e f g" , "a b d g f", "f c e g", "d g f"
    )

    presentor = DirectlyFollowsPresentor(log)
    presentor.plot()
    plt.show()