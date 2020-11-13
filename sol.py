import random
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple, Union
import time

random.seed("witch brews")

Ingredients = Tuple[int, ...]


def log(x):
    print(x, file=sys.stderr, flush=True)


@dataclass(frozen=True)
class Action:
    action_id: int
    delta: Tuple[int, int, int, int]


@dataclass(frozen=True)
class Brew(Action):
    price: int


@dataclass(frozen=True)
class Spell(Action):
    castable: bool
    repeatable: bool


@dataclass(frozen=True)
class Learn(Action):
    tome_index: int
    tax_count: int
    repeatable: bool


class Rest:
    pass


@dataclass(frozen=True)
class Witch:
    inventory: Tuple[int, ...]
    spells: Tuple[Spell, ...]


def can_brew(w: Witch, order: Brew) -> bool:
    return all(i >= -d for i, d in zip(w.inventory, order.delta))


def can_spell(w: Witch, spell: Spell) -> bool:
    if not spell.castable:
        return False
    if any(i + d < 0 for i, d in zip(w.inventory, spell.delta)):
        return False
    if sum(w.inventory) + sum(spell.delta) > 10:
        return False
    return True


def add_inventories(x: Ingredients, y: Ingredients) -> Ingredients:
    result: Ingredients = tuple(map(lambda t: t[0] + t[1], zip(x, y)))  # type: ignore
    return result


def bfs_fastest_brew(
    start_witch: Witch, orders: List[Brew], deadline
) -> Tuple[List[Union[Rest, Spell]], Union[Brew, str]]:
    queue = [start_witch]
    prev = {start_witch: None}
    actions: Dict[Witch, Union[Rest, Spell]] = {start_witch: None}  # type: ignore
    visited = {start_witch}
    iterations = 0
    while queue:
        iterations += 1
        if time.time() >= deadline:
            return [], f"time out {iterations} moves"
        cur = queue.pop(0)

        # break
        can_brew_something = False
        o = None
        for o in orders:
            if can_brew(cur, o):
                can_brew_something = True
                break
        if can_brew_something:
            result = []
            while cur is not None:
                action = actions[cur]
                if action is None:
                    break
                result.append(action)
                cur = prev[cur]  # type: ignore
            return result, o

        # cast
        for i, spell in enumerate(cur.spells):
            if not spell.castable:
                continue
            new_spells = tuple(
                [
                    Spell(
                        action_id=s.action_id,
                        delta=s.delta,
                        castable=False
                        if spell.action_id == s.action_id
                        else s.castable,
                        repeatable=s.repeatable,
                    )
                    for s in cur.spells
                ]
            )
            new_witch = Witch(
                inventory=add_inventories(cur.inventory, spell.delta), spells=new_spells
            )
            if any(item < 0 for item in new_witch.inventory):
                continue
            if new_witch in visited:
                continue
            queue.append(new_witch)
            prev[new_witch] = cur  # type: ignore
            actions[new_witch] = spell
            visited.add(new_witch)
        # rest
        all_castable = tuple(
            [
                Spell(
                    action_id=s.action_id,
                    delta=s.delta,
                    castable=True,
                    repeatable=s.repeatable,
                )
                for s in cur.spells
            ]
        )
        rested_witch = Witch(inventory=cur.inventory, spells=tuple(all_castable))
        if rested_witch not in visited:
            queue.append(rested_witch)
            prev[rested_witch] = cur  # type: ignore
            actions[rested_witch] = Rest()
            visited.add(rested_witch)
    return [], f"not found after {iterations} moves"


def main() -> None:
    while True:
        orders: List[Brew] = []
        spells: List[Spell] = []
        learns: List[Learn] = []

        action_count = int(input())
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
                orders.append(
                    Brew(
                        action_id=action_id,
                        delta=(delta_0, delta_1, delta_2, delta_3),
                        price=price,
                    )
                )
            elif action_type == "CAST":
                spells.append(
                    Spell(
                        action_id=action_id,
                        delta=(delta_0, delta_1, delta_2, delta_3),
                        castable=castable,
                        repeatable=repeatable,
                    )
                )
            elif action_type == "LEARN":
                learns.append(
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

        deadline = time.time() + 0.040

        my_witch = Witch(inventory=tuple(inventory), spells=tuple(spells))

        max_price = 0
        max_ind = 0
        for i, a in enumerate(orders):
            remaining = (a + b for a, b in zip(inventory, a.delta))
            can_afford = all(x >= 0 for x in remaining)
            if can_afford and a.price > max_price:
                max_price = a.price
                max_ind = a.action_id

        #   BREW <id>
        # | CAST <id> [<times>]
        # | LEARN <id>
        # | REST
        # | WAIT
        if max_price > 0:
            print(f"BREW {max_ind}")
        else:
            result, order = bfs_fastest_brew(
                my_witch,
                orders=orders,
                deadline=deadline,
            )
            if result:
                first = result[-1]
                countdown = f"M{len(result)} to {order.action_id}"  # type: ignore
                if isinstance(first, Rest):
                    print(f"REST {countdown}")  # type: ignore
                else:
                    print(f"CAST {first.action_id} {countdown}")
            else:
                out_string = order
                if any(can_spell(my_witch, s) for s in spells):
                    random_spell = random.choice(
                        [s for s in spells if can_spell(my_witch, s)]
                    )
                    print(f"CAST {random_spell.action_id} |{out_string}")
                else:
                    print(f"REST {out_string}")


if __name__ == "__main__":
    main()
