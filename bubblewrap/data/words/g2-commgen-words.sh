#!/bin/sh
cat << EOF
G := Group<a,b,c,d,k|k^-1*a*b*a^-1*b^-1,k*c*d*c^-1*d^-1>;
A<a,b,c,d,k> := AutomaticGroup(G);
Seq(A, 0, $1 : Search := "BFS");
EOF