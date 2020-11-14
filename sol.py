import random
import sys
from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Tuple, Union
import time

random.seed("witch brews")


def log(x):
    print(x, file=sys.stderr, flush=True)


class BaseAction:
    def smart_action(self, msg="") -> None:
        if isinstance(self, Brew):
            self.brew(msg)
        elif isinstance(self, Cast):
            self.cast(msg)
        elif isinstance(self, Learn):
            self.learn(msg)
        elif isinstance(self, Rest):
            self.rest(msg)
        else:
            raise ValueError(f"Unknown action {self}")


@dataclass(frozen=True)
class Action(BaseAction):
    action_id: int
    delta: Tuple[int, ...]


@dataclass(frozen=True)
class Brew(Action):
    price: int

    def brew(self, msg: str = "") -> None:
        print(f"BREW {self.action_id} {msg}")


@dataclass(frozen=True)
class Cast(Action):
    castable: bool
    repeatable: bool

    def cast(self, msg: str = "") -> None:
        if msg and msg[0].isdigit():
            msg = "|" + msg
        print(f"CAST {self.action_id} {msg}")


@dataclass(frozen=True)
class Learn(Action):
    tome_index: int
    tax_count: int
    repeatable: bool

    def is_freecast(self) -> bool:
        return all(d >= 0 for d in self.delta)

    def learn(self, msg: str = "") -> None:
        print(f"LEARN {self.action_id} {msg}")


@dataclass(frozen=True)
class Rest(BaseAction):
    def rest(self, msg: str = "") -> None:
        print(f"REST {msg}")


@dataclass(frozen=True)
class Witch:
    inventory: Tuple[int, ...]
    casts: Tuple[Cast, ...]

    def can_brew(self, brew: Brew) -> bool:
        return all(i >= -d for i, d in zip(self.inventory, brew.delta))

    def can_cast(self, cast: Cast) -> bool:
        if not cast.castable:
            return False
        if any(i + d < 0 for i, d in zip(self.inventory, cast.delta)):
            return False
        if sum(self.inventory) + sum(cast.delta) > 10:
            return False
        return True

    def available_casts(self) -> List[Cast]:
        return [c for c in self.casts if self.can_cast(c)]

    def cast(self, cast: Cast) -> "Witch":
        new_casts = tuple(
            replace(c, castable=False) if c == cast else c for c in self.casts
        )
        new_inventory = add_inventories(self.inventory, cast.delta)
        return replace(self, inventory=new_inventory, casts=new_casts)

    def rest(self) -> "Witch":
        return replace(self, casts=tuple(replace(c, castable=True) for c in self.casts))

    def learn(self, learn: Learn) -> "Witch":
        new_casts = self.casts + (
            Cast(
                action_id=77777,
                delta=learn.delta,
                castable=True,
                repeatable=learn.repeatable,
            ),
        )
        return replace(
            self,
            inventory=add_inventories(self.inventory, (learn.tax_count, 0, 0, 0)),
            casts=new_casts,
        )


def add_inventories(x: Tuple[int, ...], y: Tuple[int, ...]) -> Tuple[int, ...]:
    return tuple(map(sum, zip(x, y)))


BfsActions = Union[Rest, Cast, Learn]


@dataclass(frozen=True)
class BfsSuccess:
    actions: List[BfsActions]
    target: Brew


@dataclass(frozen=True)
class BfsFailure:
    message: str


def bfs_fastest_brew(
    start_witch: Witch, brews: List[Brew], learns: List[Learn], deadline
) -> Union[BfsSuccess, BfsFailure]:
    queue = [start_witch]
    prev: Dict[Witch, Optional[Witch]] = {start_witch: None}
    actions: Dict[Witch, Optional[BfsActions]] = {start_witch: None}
    iterations = 0
    while queue:
        iterations += 1
        if time.time() >= deadline:
            return BfsFailure(f"T/O {iterations}M")
        cur = queue.pop(0)

        # break
        can_brew_something = False
        o = None
        for o in brews:
            if cur.can_brew(o):
                can_brew_something = True
                break
        if can_brew_something:
            result: List[BfsActions] = []
            backtrack: Optional[Witch] = cur
            while backtrack is not None:
                action = actions[backtrack]
                if action is None:
                    break
                result.append(action)
                backtrack = prev[backtrack]
            return BfsSuccess(result, o)

        # learn
        if iterations == 1 and learns:
            first_tome = learns[0]
            if first_tome.tax_count > 0:
                new_witch = cur.learn(first_tome)
                if new_witch in prev:
                    continue
                queue.append(new_witch)
                prev[new_witch] = cur
                actions[new_witch] = first_tome
        # cast
        for cast in cur.casts:
            if not cur.can_cast(cast):
                continue
            new_witch = cur.cast(cast)
            if new_witch in prev:
                continue
            queue.append(new_witch)
            prev[new_witch] = cur
            actions[new_witch] = cast
        # rest
        all_castable = tuple(
            [
                Cast(
                    action_id=c.action_id,
                    delta=c.delta,
                    castable=True,
                    repeatable=c.repeatable,
                )
                for c in cur.casts
            ]
        )
        rested_witch = Witch(inventory=cur.inventory, casts=tuple(all_castable))
        if rested_witch not in prev:
            queue.append(rested_witch)
            prev[rested_witch] = cur
            actions[rested_witch] = Rest()
    return BfsFailure(f"not found after {iterations} moves")


class GameInput:
    def __init__(self) -> None:
        self.brews: List[Brew] = []
        self.learns: List[Learn] = []
        self.my_witch: Witch

    def read(self):
        action_count = int(input())
        casts: List[Cast] = []
        for i in range(action_count):
            # action_id: the unique ID of this spell or recipe
            # action_type: CAST, OPPONENT_CAST, LEARN, BREW
            # delta_x: tier-x ingredient change
            # price: the price in rupees if this is a potion
            # tome_index: the index in the tome if this is a tome spell,
            #   equal to the read-ahead tax
            # tax_count: the amount of taxed tier-0 ingredients you gain
            #   from learning this spell
            # castable: 1 if this is a castable player spell
            # repeatable: 1 if this is a repeatable player spell
            (
                action_id_str,
                action_type,
                delta_0_str,
                delta_1_str,
                delta_2_str,
                delta_3_str,
                price_str,
                tome_index_str,
                tax_count_str,
                castable_str,
                repeatable_str,
            ) = input().split()
            action_id = int(action_id_str)
            delta_0 = int(delta_0_str)
            delta_1 = int(delta_1_str)
            delta_2 = int(delta_2_str)
            delta_3 = int(delta_3_str)
            price = int(price_str)
            tome_index = int(tome_index_str)
            tax_count = int(tax_count_str)
            castable = castable_str != "0"
            repeatable = repeatable_str != "0"

            if action_type == "BREW":
                self.brews.append(
                    Brew(
                        action_id=action_id,
                        delta=(delta_0, delta_1, delta_2, delta_3),
                        price=price,
                    )
                )
            elif action_type == "CAST":
                casts.append(
                    Cast(
                        action_id=action_id,
                        delta=(delta_0, delta_1, delta_2, delta_3),
                        castable=castable,
                        repeatable=repeatable,
                    )
                )
            elif action_type == "LEARN":
                self.learns.append(
                    Learn(
                        action_id=action_id,
                        delta=(delta_0, delta_1, delta_2, delta_3),
                        tome_index=tome_index,
                        tax_count=tax_count,
                        repeatable=repeatable,
                    )
                )
        *inventory, score = [int(j) for j in input().split()]
        _ = [int(j) for j in input().split()]  # other player
        self.my_witch = Witch(inventory=tuple(inventory), casts=tuple(casts))


def most_expensive_possible_brew(w: Witch, brews: List[Brew]) -> Optional[Brew]:
    max_price = 0
    max_brew = None
    for b in brews:
        remaining = add_inventories(w.inventory, b.delta)
        can_afford = all(x >= 0 for x in remaining)
        if can_afford and b.price > max_price:
            max_price = b.price
            max_brew = b
    return max_brew


def maybe_learn_something(
    w: Witch, learns: List[Learn]
) -> Tuple[Union[Learn, Cast, Rest, None], str]:
    freecasts = [t for t in learns if t.is_freecast()]
    first_tome = [t for t in learns if t.tome_index == 0]
    if len(w.casts) < 7 and freecasts:
        first_freecast = min(freecasts, key=lambda t: t.tome_index)
        can_afford_learn = first_freecast.tome_index <= w.inventory[0]
        if can_afford_learn:
            return first_freecast, "grab freecast!"
        else:
            double_blue = [c for c in w.casts if c.delta == (2, 0, 0, 0)][0]
            if double_blue.castable:
                return double_blue, f"need to learn {first_freecast.action_id}"
            else:
                return Rest(), "need more blues"
    elif len(w.casts) < 6 and learns:
        return first_tome[0], "grab something..."
    return None, ""


def main() -> None:
    while True:

        game = GameInput()
        game.read()
        start_time = time.time()

        max_brew = most_expensive_possible_brew(game.my_witch, game.brews)
        learn_result, msg = maybe_learn_something(game.my_witch, game.learns)
        if learn_result:
            learn_result.smart_action(msg)
        elif max_brew:
            max_brew.brew("BREW!")
        else:
            result = bfs_fastest_brew(
                game.my_witch,
                brews=game.brews,
                learns=game.learns,
                deadline=start_time + 0.040,
            )
            if isinstance(result, BfsSuccess):
                delta_time = time.time() - start_time
                delta_time_str = f"{delta_time*1000:.0f}ms"
                price = result.target.price
                countdown_text = f"T-{len(result.actions)} {price}💎 {delta_time_str}"
                first = result.actions[-1]
                if isinstance(first, Rest):
                    first.rest(countdown_text)
                elif isinstance(first, Cast):
                    first.cast(countdown_text)
                elif isinstance(first, Learn):
                    first.learn(f"{countdown_text} + learning!")
                else:
                    raise ValueError(f"Unknown action from BFS: {first}")
            else:
                if game.my_witch.available_casts():
                    random_cast = random.choice(game.my_witch.available_casts())
                    random_cast.cast(result.message + " -> cast random")
                else:
                    Rest().rest(result.message + " -> rest")


if __name__ == "__main__":
    main()
