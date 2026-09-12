"""
This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see <https://www.gnu.org/licenses/>.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class AST:
  func: str
  args: tuple[AST, ...]

  def __repr__(self) -> str:
    if len(self.args) == 0: return self.func
    return "(" + " ".join([self.func] + list(map(repr, self.args))) + ")"

def parse(src) -> AST:
  tokens = src.replace("(", " ( ").replace(")", " ) ").split()
  state: list[list[AST]] = [[]]
  for t in tokens:
    if t == '(':
      state.append([])
    elif t == ')':
      last = state.pop()
      assert len(last) > 0
      assert len(last[0].args) == 0
      state[-1].append(AST(last[0].func, tuple(last[1:])))
    else:
      state[-1].append(AST(t, ()))
  return state[0][0]


EClass = int

@dataclass(frozen=True)
class ENode:
  func: str
  args: tuple[EClass, ...]

  def __repr__(self) -> str:
    return "(" + " ".join([self.func] + list(map(str, self.args))) + ")"


Subst = dict[str, EClass]


class EGraph:
  uf: dict[EClass, EClass]
  hashcons: dict[ENode, EClass]
  hashcons_inv: dict[EClass, ENode]
  parents: dict[EClass, list[EClass]]
  group: dict[EClass, dict[str, list[EClass]]]
  classes: set[EClass]

  def __init__(self):
    self.uf = {}
    self.hashcons = {}
    self.hashcons_inv = {}
    self.parents = {}
    self.group = {}
    self.classes = set()

  def add_expr(self, node: AST) -> EClass:
    return self.add(ENode(node.func, tuple(map(self.add_expr, node.args))))

  def add(self, enode: ENode) -> EClass:
    if enode in self.hashcons: return self.find(self.hashcons[enode])
    id = len(self.uf)
    self.uf[id] = id
    self.hashcons[enode] = id
    self.hashcons_inv[id] = enode
    self.parents[id] = []
    self.group[id] = { enode.func: [id] }
    self.classes.add(id)
    for a in enode.args: self.parents[a].append(id)
    return id

  def find(self, eclass: EClass) -> EClass:
    parent = self.uf[eclass]
    if parent == eclass: return parent
    else:
      root = self.find(parent)
      self.uf[eclass] = root
      return root

  def canonicalize(self, enode: ENode) -> ENode:
    return ENode(enode.func, tuple(map(self.find, enode.args)))

  def union(self, e0: EClass, e1: EClass):
    e0 = self.find(e0)
    e1 = self.find(e1)
    if e0 == e1: return None
    e0, e1 = (e0, e1) if e0 > e1 else (e1, e0)
    self.uf[e0] = e1
    for func, enodes in self.group[e0].items():
      self.group[e1][func] = self.group[e1].get(func, []) + enodes
    del self.group[e0]
    self.classes.remove(e0)
    for enode_id in self.parents[e0]:
      canon_id = self.add(self.canonicalize(self.hashcons_inv[enode_id]))
      self.union(canon_id, enode_id)

  def match(self, pattern: AST, eclass: EClass, subs: Iterable[Subst]) -> Iterable[Subst]:
    result = []
    if pattern.func.startswith("?"):
      var = pattern.func
      assert len(pattern.args) == 0
      for s in subs:
        if var in s and self.find(s[var]) == self.find(eclass): result.append(s)
        elif var not in s: s = s.copy(); s[var] = eclass; result.append(s)
    else:
      from functools import reduce
      for enode_id in self.group[self.find(eclass)].get(pattern.func, []):
        enode = self.hashcons_inv[enode_id]
        assert len(enode.args) == len(pattern.args)
        if all(map(lambda a: a == self.find(a), enode.args)):
          result += reduce(lambda subs, i: self.match(pattern.args[i], enode.args[i], subs),
                           range(len(enode.args)),
                           subs)
    return result

  def match_all(self, pattern) -> Iterable[Subst]:
    from itertools import chain
    return chain.from_iterable(map(lambda c: self.match(pattern, c, [{}]), self.classes))

  def add_pattern(self, pattern: AST, sub: Subst) -> EClass:
    if pattern.func.startswith("?"):
      assert pattern.func in sub
      return sub[pattern.func]
    else:
      return self.add(ENode(pattern.func, tuple(map(lambda a: self.add_pattern(a, sub), pattern.args))))

  def saturate(self, rules: list[tuple[AST, AST]], steps=2):
    for _ in range(steps):
      to_union: list[tuple[EClass, EClass]] = []
      for (lhs, rhs) in rules:
        for subst in list(egraph.match_all(lhs)):
          lhsid = egraph.add_pattern(lhs, subst)
          rhsid = egraph.add_pattern(rhs, subst)
          to_union.append((lhsid, rhsid))
      for (lid, rid) in to_union:
        egraph.union(lid, rid)

  def extract(self, eclass: EClass) -> tuple[AST, float]:
    from math import inf
    cost: dict[EClass, float] = { eclass: inf for eclass in self.classes }
    canons: dict[EClass, ENode] = {}

    changed = True
    while changed:
      changed = False
      for cls in self.classes:
        for _, enodes in self.group[cls].items():
          for enodeid in enodes:
            enode = self.hashcons_inv[enodeid]
            c = (1 if enode.func == "or" else 1) + sum(cost[self.find(a)] for a in enode.args)
            if c < cost[cls]:
              cost[cls] = c
              canons[cls] = enode
              changed = True

    def do_extract(eclass) -> AST:
      c = canons[self.find(eclass)]
      return AST(c.func, tuple(map(do_extract, c.args)))

    return (do_extract(eclass), cost[self.find(eclass)])


egraph = EGraph()

rules = list(map(lambda x: (parse(x[0]), parse(x[1])), [
  # Not stuff
  ("(not true)", "false"),
  ("(not false)", "true"),
  ("(and ?x (not ?x))", "false"),
  ("(not (not ?x))", "?x"),
  ("?x", "(not (not ?x))"),
  ("(or ?x (not ?x))", "true"),

  # DeMorgan
  ("(not (and ?x ?y))", "(or (not ?x) (not ?y))"),
  ("(or (not ?x) (not ?y))", "(not (and ?x ?y))"),
  ("(not (or ?x ?y))", "(and (not ?x) (not ?y))"),
  ("(and (not ?x) (not ?y))", "(not (or ?x ?y))"),

  # Idempotent
  ("(or ?x ?x)", "?x"),
  ("(and ?x ?x)", "?x"),

  # Units
  ("(and true ?x)", "?x"),
  ("(and false ?x)", "false"),
  ("(or true ?x)", "true"),
  ("(or false ?x)", "false"),

  # Commutative
  ("(and ?x ?y)", "(and ?y ?x)"),
  ("(or ?x ?y)", "(or ?y ?x)"),

  # Associative
  ("(and ?x (and ?y ?z))", "(and (and ?x ?y) ?z)"),
  ("(and (and ?x ?y) ?z)", "(and ?x (and ?y ?z))"),
  ("(or ?x (or ?y ?z))", "(or (or ?x ?y) ?z)"),
  ("(or (or ?x ?y) ?z)", "(or ?x (or ?y ?z))"),

  # Distributive
  ("(and ?x (or ?y ?z))", "(or (and ?x ?y) (and ?x ?z))"),
  ("(or ?x (and ?y ?z))", "(and (or ?x ?y) (or ?x ?z))"),

  # Optimization
  ("(and ?x (or ?x ?y))", "?x"),
]))

src = parse("""
  (or
    (not
      (and
        (not (or x (f x)))
        (or (not x) (not (f x)))))
    (f x))
""")
srcid = egraph.add_expr(src)

egraph.saturate(rules, steps=4)

best, size = egraph.extract(srcid)

print("Source =", src)
print("Best   =", best)
print("Cost   =", size)
