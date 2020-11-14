import random
import sys
from typing import Dict, List, NamedTuple, Optional, Tuple, Union
import time

random.seed("witch brews")


def log(x):
    print(x, file=sys.stderr, flush=True)


class Brew(NamedTuple):
    action_id: int
    delta: Tuple[int, ...]
    price: int

    def brew(self, msg: str = "") -> None:
        print(f"BREW {self.action_id} {msg}")


class Cast(NamedTuple):
    action_id: int
    delta: Tuple[int, ...]
    castable: bool
    repeatable: bool

    def cast(self, msg: str = "") -> None:
        if msg and msg[0].isdigit():
            msg = "|" + msg
        print(f"CAST {self.action_id} {msg}")


class Learn(NamedTuple):
    action_id: int
    delta: Tuple[int, ...]
    tome_index: int
    tax_count: int
    repeatable: bool

    def is_freecast(self) -> bool:
        return all(d >= 0 for d in self.delta)

    def learn(self, msg: str = "") -> None:
        print(f"LEARN {self.action_id} {msg}")


class Rest:
    def rest(self, msg: str = "") -> None:
        print(f"REST {msg}")


class Witch(NamedTuple):
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
            c._replace(castable=False) if c == cast else c for c in self.casts
        )
        new_inventory = add_inventories(self.inventory, cast.delta)
        return self._replace(inventory=new_inventory, casts=new_casts)

    def rest(self) -> "Witch":
        return self._replace(casts=tuple(c._replace(castable=True) for c in self.casts))

    def can_learn(self, learn: Learn) -> bool:
        return self.inventory[0] >= learn.tome_index

    def learn(self, learn: Learn) -> "Witch":
        new_casts = self.casts + (
            Cast(
                action_id=77777,
                delta=learn.delta,
                castable=True,
                repeatable=learn.repeatable,
            ),
        )
        add_blues = min(learn.tax_count, 10 - sum(self.inventory))
        return self._replace(
            inventory=add_inventories(self.inventory, (add_blues, 0, 0, 0)),
            casts=new_casts,
        )


def add_inventories(x: Tuple[int, ...], y: Tuple[int, ...]) -> Tuple[int, ...]:
    return tuple(map(sum, zip(x, y)))


def mul_inventories(x: Tuple[int, ...], y: Tuple[int, ...]) -> Tuple[int, ...]:
    return tuple(map(lambda t: t[0] * t[1], zip(x, y)))


BfsActions = Union[Rest, Cast, Learn]


class BfsSuccess(NamedTuple):
    actions: List[BfsActions]
    target: Brew


class BfsFailure(NamedTuple):
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
        rested_witch = cur.rest()
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


def learn_profit(learn: Learn, w: Witch, turn) -> Tuple[float, int]:
    average_game_length = 50
    expected_turns_left = average_game_length - turn
    learn_diminishing_coefficient = (
        0.0 if expected_turns_left < 0 else expected_turns_left / average_game_length
    )

    weights = (1, 3, 5, 7)  # за сколько ходов делается 2 шт. на стандартных рецептах
    freecast_bonus = 10

    result = freecast_bonus if learn.is_freecast() else 0
    result += sum(mul_inventories(learn.delta, weights))

    free_slots = 10 - sum(w.inventory)
    result += min(learn.tax_count, free_slots)

    result -= learn.tome_index

    return result * learn_diminishing_coefficient, result


def main() -> None:
    turn = 0
    while True:
        turn += 1

        game = GameInput()
        game.read()
        start_time = time.time()

        profit_worth_to_learn = 5
        learn_table = [
            (*learn_profit(s, game.my_witch, turn), game.my_witch.can_learn(s), s)
            for s in game.learns
        ]
        learn_table = [
            (p, orig, can, learn)
            for (p, orig, can, learn) in learn_table
            if p > profit_worth_to_learn
        ]
        learn_table.sort(key=lambda x: x[0], reverse=True)
        can_learn_table = [
            (p, orig, can, learn) for (p, orig, can, learn) in learn_table if can
        ]
        log(learn_table)
        log(can_learn_table)

        max_brew = most_expensive_possible_brew(game.my_witch, game.brews)

        if can_learn_table:
            profit, orig, _, best_learn = can_learn_table[0]
            best_learn.learn(f"learn profit {profit}(base={orig})")
        elif learn_table:
            double_blue = [c for c in game.my_witch.casts if c.delta == (2, 0, 0, 0)][0]
            if double_blue.castable:
                double_blue.cast(f"need to learn {learn_table[0][3].action_id}")
            else:
                Rest().rest("need more blues")
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
                first_tome = (
                    [t for t in game.learns if t.tome_index == 0][0]
                    if game.learns
                    else None
                )
                if (
                    game.learns
                    and first_tome
                    and first_tome.tax_count >= 3
                    and sum(game.my_witch.inventory) <= 7
                ):
                    first_tome.learn(" -> get some tax at least")
                elif game.my_witch.available_casts():
                    random_cast = random.choice(game.my_witch.available_casts())
                    random_cast.cast(result.message + " -> cast random")
                else:
                    Rest().rest(result.message + " -> rest")


if __name__ == "__main__":
    main()
