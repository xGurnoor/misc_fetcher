# MIT License

# Copyright (c) [2024] [Gurnoor Singh]

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Script to calculate cash loss and left based on cash hired and guessed percentage took."""
from argparse import ArgumentParser
from util.utils import convert_to_human


parser = ArgumentParser(
    description="Calcuates total cash taken based on total tut value hired,"
    "hits done and percentage taken.")


history = []


def calculate(t, hits, per):
    """Calculates the actual cash lost"""
    lost = 0
    for _ in range(hits):
        loss = (per/100) * t
        lost += loss
        t -= loss
        history.append((t, loss))
    return (lost, t)


def calc(t, hits, per, show_history):
    """Wrapper over the calculate function"""
    s = calculate(t, hits, per)
    lost = convert_to_human(s[0])
    left = convert_to_human(s[1])
    if show_history:
        for x in history:
            t1 = convert_to_human(x[0])
            loss = convert_to_human(x[1])
            print(f"Total: ${t1} Lost: ${loss}")
    print(f"Lost: ${lost} Left: ${left}")


parser.add_argument('hits', type=int, help="Total hits done")
parser.add_argument('percentage', type=float, help="Percentage taken per hit")
parser.add_argument('total', help="Total tutor value hired")
parser.add_argument('-H', '--history', required=False, action='store_true',
                    help="Show how the total cash changes per hits")
res = parser.parse_args()
total = res.total.lower()

if total.endswith('q'):
    total = total.replace('q', '')
    total = float(total) * 1_000_000_000_000_000
elif total.endswith('t'):
    total = total.replace('t', '')
    total = float(total) * 1_000_000_000_000
elif total.endswith('b'):
    total = total.replace('b', '')
    total = float(total) * 1_000_000_000
elif total.endswith('m'):
    total = total.replace('m', '')
    total = float(total) * 1_000_000
elif total.endswith('k'):
    total = total.replace('k', '')
    total = float(total) * 1000

calc(total, res.hits, res.percentage, res.history)
