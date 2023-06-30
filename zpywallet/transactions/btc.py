"""Class for constructing Bitcoin transactions.

Bitcoin transactions, including the segwit parts look something like this:

+------------+---------+-----------------+-----------+--------------------+--------------+------------+-----------+
|  Version   | Flag    |  Input Count    |  Inputs   | Output Count       |  Outputs     | Witness    | Locktime  |
| (4 bytes)  |(2 bytes)|  (Variable)     |           | (Variable)         |              | (Variable) | (4 bytes) |
+------------+---------+---------+-------+-----------+--------------------+--------------+------------+-----------+
          |       |   |         |                  
          v       v   v         v                  
+-------------+-------------+-------------+-------+
| Input 1     | Input 2     | Input 3     |  ...  |
| (Variable)  | (Variable)  | (Variable)  |       |
+-------------+-------------+-------------+-------+
          |       |   |         |                  
          v       v   v         v                  
Input
+------------------+-------------------+------------------+---------------+--------------+
|  Outpoint Hash   | Outpoint Index    |  Script Length   |  Script Sig   | Sequence     |
| (32 bytes)       | (4 bytes)         |  (Variable)      |   (Variable)  | (4 bytes)    |
+------------------+-------------------+------------------+---------------+--------------+
          |       |   |         |                  |
          v       v   v         v                  v
+--------+-----+-------------+---------------+------+
| Output 1     | Output 2    |  Output 3     | ...  |
| (Variable)   | (Variable)  |  (Variable)   |      |
+--------+-----+-------------+---------------+------+
          |       |   |         |
          v       v   v         v
Output
+------------------+-------------+--------------+
|  Value      |  Script Length   |  Script      |
| (8 bytes)   |  (Variable)      |  (Variable)  |
+--------------------------------+--------------+

See https://en.bitcoin.it/wiki/Transaction#General_format_of_a_Bitcoin_transaction_.28inside_a_block.29 for more detals.
In particular, "Flag" is exclusively for identifying the present of witness data and if it's omitted, so is the witness data.
"""

