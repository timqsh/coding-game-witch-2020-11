from sol import BfsSuccess, Cast, bfs_fastest_brew, Witch, Brew, main
import time


def test_bfs():
    result = bfs_fastest_brew(
        Witch(
            (3, 0, 0, 0),
            (
                Cast(777, (2, 0, 0, 0), castable=True, repeatable=False),
                Cast(888, (-1, 1, 0, 0), castable=True, repeatable=False),
                Cast(999, (0, -1, 1, 0), castable=True, repeatable=False),
                Cast(666, (0, 0, -1, 1), castable=True, repeatable=False),
            ),
        ),
        brews=[Brew(action_id=111, delta=(0, 0, 0, -4), price=100500)],
        learns=[],
        deadline=time.time() + 99999999999,
    )
    assert isinstance(result, BfsSuccess)
    assert len(result.actions) == 16


def test_bfs_repeat():
    result = bfs_fastest_brew(
        Witch(
            (3, 0, 0, 0),
            (
                Cast(777, (2, 0, 0, 0), castable=True, repeatable=False),
                Cast(888, (-1, 1, 0, 0), castable=True, repeatable=False),
                Cast(999, (0, -1, 1, 0), castable=True, repeatable=False),
                Cast(666, (0, 0, -1, 1), castable=True, repeatable=False),
                Cast(555, (-2, 2, 0, 0), castable=True, repeatable=True),
                Cast(555, (4, 0, 0, 0), castable=True, repeatable=False),
            ),
        ),
        brews=[Brew(action_id=111, delta=(0, -4, 0, 0), price=100500)],
        learns=[],
        deadline=time.time() + 99999999999,
    )
    assert isinstance(result, BfsSuccess)
    assert len(result.actions) == 2


if __name__ == "__main__":
    test_bfs()
