import random
import sys
from typing import Dict, List, NamedTuple, Optional, Tuple, Union
import time

random.seed("witch brews")


def log(x):
    print(x, file=sys.stderr, flush=True)


################
# Datastructures
################


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

    def cast(self, num: int = 1, msg: str = "") -> None:
        if msg and msg[0].isdigit():
            msg = "|" + msg
        print(f"CAST {self.action_id} {num} {msg}")


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

    # @profile
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

    # @profile
    def cast(self, cast: Cast) -> "Witch":
        new_casts = tuple(
            Cast(c.action_id, c.delta, False, c.repeatable)
            if c.action_id == cast.action_id
            else c
            for c in self.casts
        )
        new_inventory = add_inventories(self.inventory, cast.delta)
        return Witch(inventory=new_inventory, casts=new_casts)

    def rest(self) -> "Witch":
        return Witch(
            inventory=self.inventory,
            casts=tuple(
                Cast(c.action_id, c.delta, True, c.repeatable) if not c.castable else c
                for c in self.casts
            ),
        )

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
        remove_blues = learn.tome_index
        new_inventory = add_inventories(self.inventory, (-remove_blues, 0, 0, 0))
        add_blues = min(learn.tax_count, 10 - sum(new_inventory))
        return self._replace(
            inventory=add_inventories(new_inventory, (add_blues, 0, 0, 0)),
            casts=new_casts,
        )


#################
# Basic Functions
#################


def add_inventories(x: Tuple[int, ...], y: Tuple[int, ...]) -> Tuple[int, ...]:
    return tuple(map(sum, zip(x, y)))


def mul_inventories(x: Tuple[int, ...], y: Tuple[int, ...]) -> Tuple[int, ...]:
    return tuple(map(lambda t: t[0] * t[1], zip(x, y)))


######################
# Breadth First Search
######################


class BfsCast(NamedTuple):
    cast: Cast
    num: int


BfsActions = Union[Rest, BfsCast, Learn]


class BfsSuccess(NamedTuple):
    actions: List[BfsActions]
    target: Brew


class BfsFailure(NamedTuple):
    message: str


def maybe_stop_bfs(
    brews: List[Brew],
    cur: Witch,
    actions: Dict[Witch, Optional[BfsActions]],
    prev: Dict[Witch, Optional[Witch]],
) -> Union[BfsSuccess, None]:
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
    return None


# @profile
def bfs_fastest_brew(
    start_witch: Witch, brews: List[Brew], learns: List[Learn], deadline: float
) -> Union[BfsSuccess, BfsFailure]:
    "Find shortest path to some brew"
    queue = [start_witch]
    prev: Dict[Witch, Optional[Witch]] = {start_witch: None}
    actions: Dict[Witch, Optional[BfsActions]] = {start_witch: None}
    iterations = 0
    while queue:
        iterations += 1
        if time.time() >= deadline:
            return BfsFailure(f"T/O {iterations}M")
        current_witch = queue.pop(0)

        result = maybe_stop_bfs(brews, current_witch, actions, prev)
        if result is not None:
            return result

        if iterations == 1 and learns:
            for learn in learns:
                if current_witch.can_learn(learn):
                    new_witch = current_witch.learn(learn)
                    if new_witch not in prev:
                        queue.append(new_witch)
                        prev[new_witch] = current_witch
                        actions[new_witch] = learn
        for cast in current_witch.casts:
            if not current_witch.can_cast(cast):
                continue
            new_witch = current_witch.cast(cast)
            if new_witch not in prev:
                queue.append(new_witch)
                prev[new_witch] = current_witch
                actions[new_witch] = BfsCast(cast, 1)
            # multicast
            if cast.repeatable:
                cast_count = 1
                while new_witch.can_cast(cast):
                    cast_count += 1
                    new_witch = new_witch.cast(cast)
                    if new_witch not in prev:
                        queue.append(new_witch)
                        prev[new_witch] = current_witch
                        actions[new_witch] = BfsCast(cast, cast_count)
        new_witch = current_witch.rest()
        if new_witch not in prev:
            queue.append(new_witch)
            prev[new_witch] = current_witch
            actions[new_witch] = Rest()
    return BfsFailure(f"not found after {iterations} moves")


#################
# Game Input Read
#################


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


#########################
# Strategies & Heuristics
#########################


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


def spell_delta_profit(x: Union[Cast, Learn]):
    weights = (1, 3, 5, 7)  # за сколько ходов делается 2 шт. на стандартных рецептах
    return sum(mul_inventories(x.delta, weights))


def is_direct_upgrade(x: Union[Cast, Learn], y: Union[Cast, Learn]) -> bool:
    return all(xx >= yy for xx, yy in zip(x.delta, y.delta))


def learn_profit(learn: Learn, w: Witch, turn) -> Tuple[float, int]:
    already_have_direct_upgrade = any(is_direct_upgrade(c, learn) for c in w.casts)
    if already_have_direct_upgrade:
        return 0.0, 0

    average_game_length = 40
    expected_turns_left = average_game_length - turn
    learn_diminishing_coefficient = (
        0.0 if expected_turns_left < 0 else expected_turns_left / average_game_length
    )

    freecast_bonus = 10
    result = freecast_bonus if learn.is_freecast() else 0

    result += spell_delta_profit(learn)

    free_slots = 10 - sum(w.inventory)
    result += min(learn.tax_count, free_slots)

    result -= learn.tome_index

    return result * learn_diminishing_coefficient, result


###########
# Main loop
###########


def main() -> None:
    turn = 0
    while True:
        turn += 1

        game = GameInput()
        game.read()
        start_time = time.time()

        profit_worth_to_learn = 5
        profit_worth_to_make_blues_and_learn = 6
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

        max_brew = most_expensive_possible_brew(game.my_witch, game.brews)

        if max_brew:
            max_brew.brew("BREW!")
        elif can_learn_table:
            profit, orig, _, best_learn = can_learn_table[0]
            best_learn.learn(f"learn profit {profit}(base={orig})")
        elif learn_table and learn_table[0][0] > profit_worth_to_make_blues_and_learn:
            blue_generator: List[Union[Learn, Cast]] = [
                c
                for c in game.my_witch.available_casts()
                if c.delta[1] == c.delta[2] == c.delta[3] == 0
            ]
            if game.learns:
                first_tome_to_learn = [t for t in game.learns if t.tome_index == 0][0]
                if first_tome_to_learn.tax_count >= 2:
                    blue_generator.append(first_tome_to_learn)
            if blue_generator:
                best_blue_generator = max(
                    blue_generator, key=lambda i: (i.delta[0], isinstance(i, Learn))
                )
                if isinstance(best_blue_generator, Cast):
                    best_blue_generator.cast(
                        1, f"get blues to learn {learn_table[0][3].action_id}"
                    )
                else:
                    best_blue_generator.learn(
                        f"learn to get blues to learn {learn_table[0][3].action_id} 😎"
                    )
            else:
                Rest().rest(f"need more blues to learn {learn_table[0][3].action_id}")
        else:
            # log(
            #     (
            #         game.my_witch,
            #         game.brews,
            #         game.learns,
            #     )
            # )
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
                elif isinstance(first, BfsCast):
                    msg = countdown_text
                    if first.num > 1:
                        msg += " + MULTICAST!!!"
                    first.cast.cast(first.num, msg)
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
                    first_tome.learn(result.message + " -> get some tax at least")
                elif game.my_witch.available_casts():
                    best_cast = max(
                        game.my_witch.available_casts(), key=spell_delta_profit
                    )
                    best_cast.cast(1, result.message + " -> cast best (i think)")
                else:
                    Rest().rest(result.message + " -> can't cast -> rest")


if __name__ == "__main__":
    main()
