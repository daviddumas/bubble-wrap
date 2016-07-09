#!/bin/sh
cat << EOF
G := Group<a,b,c,d|a*b*a^-1*b^-1*c*d*c^-1*d^-1>;
A<a,b,c,d> := AutomaticGroup(G);
Seq(A, 0, $1 : Search := "BFS");
EOF