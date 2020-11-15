from sol import BfsSuccess, Cast, bfs_fastest_brew, Witch, Brew, Learn
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


def test_bfs_timeout():
    params = (
        Witch(
            inventory=(0, 0, 0, 0),
            casts=(
                Cast(
                    action_id=82, delta=(2, 0, 0, 0), castable=False, repeatable=False
                ),
                Cast(
                    action_id=83, delta=(-1, 1, 0, 0), castable=True, repeatable=False
                ),
                Cast(
                    action_id=84, delta=(0, -1, 1, 0), castable=True, repeatable=False
                ),
                Cast(
                    action_id=85, delta=(0, 0, -1, 1), castable=True, repeatable=False
                ),
                Cast(
                    action_id=88, delta=(-3, 3, 0, 0), castable=False, repeatable=True
                ),
                Cast(action_id=90, delta=(1, 0, 1, 0), castable=True, repeatable=False),
                Cast(action_id=93, delta=(-4, 0, 2, 0), castable=True, repeatable=True),
                Cast(action_id=96, delta=(0, 0, 0, 1), castable=True, repeatable=False),
                Cast(
                    action_id=100, delta=(1, 1, 0, 0), castable=False, repeatable=False
                ),
                Cast(
                    action_id=101, delta=(-5, 0, 0, 2), castable=True, repeatable=True
                ),
                Cast(
                    action_id=102, delta=(-3, 0, 0, 1), castable=True, repeatable=True
                ),
                Cast(
                    action_id=103, delta=(3, -1, 0, 0), castable=True, repeatable=True
                ),
                Cast(
                    action_id=104, delta=(3, 0, 0, 0), castable=True, repeatable=False
                ),
            ),
        ),
        [
            Brew(action_id=58, delta=(0, -3, 0, -2), price=17),
            Brew(action_id=56, delta=(0, -2, -3, 0), price=14),
            Brew(action_id=75, delta=(-1, -3, -1, -1), price=16),
            Brew(action_id=67, delta=(0, -2, -1, -1), price=12),
            Brew(action_id=57, delta=(0, 0, -2, -2), price=14),
        ],
        [
            Learn(
                action_id=24,
                delta=(0, 3, 0, -1),
                tome_index=0,
                tax_count=1,
                repeatable=True,
            ),
            Learn(
                action_id=39,
                delta=(0, 0, -2, 2),
                tome_index=1,
                tax_count=1,
                repeatable=True,
            ),
            Learn(
                action_id=7,
                delta=(3, 0, 1, -1),
                tome_index=2,
                tax_count=0,
                repeatable=True,
            ),
            Learn(
                action_id=19,
                delta=(0, 2, -1, 0),
                tome_index=3,
                tax_count=0,
                repeatable=True,
            ),
            Learn(
                action_id=32,
                delta=(1, 1, 3, -2),
                tome_index=4,
                tax_count=0,
                repeatable=True,
            ),
            Learn(
                action_id=38,
                delta=(-2, 2, 0, 0),
                tome_index=5,
                tax_count=0,
                repeatable=True,
            ),
        ],
    )
    result = bfs_fastest_brew(*params, deadline=time.time() + 9999999)
    assert isinstance(result, BfsSuccess)
    assert len(result.actions) == 5


if __name__ == "__main__":
    # test_bfs()
    test_bfs_timeout()
