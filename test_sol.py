from sol import Spell, bfs_fastest_brew, Witch, Brew
import time


def test_bfs():
    result, _ = bfs_fastest_brew(
        Witch(
            inventory=(1, 0, 0, 0),
            spells=tuple(
                [
                    Spell(
                        action_id=1, delta=(-1, 0, 0, 1), castable=True, repeatable=True
                    )
                ]
            ),
        ),
        [Brew(action_id=777, delta=(0, 0, 0, 1), price=100500)],
        deadline=time.time() + 0.40,
    )
    assert result == []


def test_bfs2():
    result = bfs_fastest_brew(
        Witch(
            inventory=(3, 0, 0, 0),
            spells=tuple(
                [
                    Spell(action_id=78, delta=(2, 0, 0, 0), price=0, castable=True),
                    Spell(action_id=79, delta=(-1, 1, 0, 0), price=0, castable=True),
                    Spell(action_id=80, delta=(0, -1, 1, 0), price=0, castable=True),
                    Spell(action_id=81, delta=(0, 0, -1, 1), price=0, castable=True),
                ]
            ),
        ),
        [(2, 0, 1, 1), (1, 1, 1, 3), (0, 0, 5, 0), (0, 0, 3, 2), (0, 0, 2, 2)],
    )
    assert len(result) > 0
