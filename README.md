I presented Greg Nelson's PhD thesis for Papers We Love Zurich.
Half of the presentation was me live coding an e-graph from scratch in Python for optimizing boolean expressions.

This repository contains the source code of the e-graph.
It is a self-contained Python3 script with no external dependencies.
So just run `python3 egraph.py` to try it.

# Talk Abstract

In this session, [George Zakhour](https://grgz.me/), a PhD student at the Programming Group at the University of St.Gallen will present ["Techniques for Program Verification"](https://scottmcpeak.com/nelson-verification.pdf), focusing particularly on e-graphs.

E-graphs are at the heart of SMT solvers, a cornerstone of automated reasoning that powers applications from program verification to automated theorem proving. They are used for efficiently maintaining equalities and equivalence relations. Originally introduced in Greg Nelson's seminal 1980 PhD thesis, they gained widespread popularity for compiler optimization, program synthesis, and software testing thanks to the egg library (POPL' 21). In this talk, we will revisit Nelson's thesis, implement an e-graph live from scratch, and put it to work.

Why care?

* **For verification enthusiasts**: the e-graph is the congruence closure that propagates equalities from one theory to all the others. They allow you to build a large theory compositionally from smaller ones.
* **For type system enthusiasts**: e-graphs are the solvers of type inference constraints.
* **For compiler enthusiasts**: e-graphs eliminate phase ordering by searching many equivalent program optimizations at once.

The talk will be 45–60 minutes, followed by discussion, Q&A and snacks. No prior background in SMTs is required; basic familiarity with compilers and formal methods will help.

**Link**: [https://www.meetup.com/papers-we-love-zurich/events/316048029](https://www.meetup.com/papers-we-love-zurich/events/316048029)

**Slides**: [https://grgz.me/pwl-slides.pdf](https://grgz.me/pwl-slides.pdf)
