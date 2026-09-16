"""Handwritten, fact-checked curriculum. No synthetic user history is seeded."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Concept, ConceptDependency, LearningPath, Mastery, Subject, Topic
from app.schemas import CardData
from app.services.content import store_card

# id, topic, title, difficulty, prerequisites, hook, explanation, example, takeaway, equation,
# question/choices/correct/explanation, transfer question/choices/correct/explanation
CURRICULUM = [
    (
        "complexity",
        "algorithms",
        "Thinking in Big O",
        0.2,
        [],
        "Twice the data doesn't always mean twice the work.",
        "Big O describes how an algorithm's work grows as the input grows. A single lookup in an array takes constant time, O(1). Scanning the array takes linear time, O(n). We ignore constant factors to focus on the shape of growth. Big O is an upper bound, not an exact stopwatch reading.",
        "Checking every name on a guest list takes n checks in the worst case. Two separate scans take 2n checks, still O(n). A scan inside another full scan takes n × n checks: O(n²).",
        "Count how the work grows, not how many milliseconds one run takes.",
        r"T(n)=3n+7\quad\Rightarrow\quad O(n)",
        (
            "An algorithm checks every item once. If the input doubles, its work roughly…",
            ["Stays the same", "Doubles", "Quadruples", "Drops by half"],
            1,
            "One operation per item gives n operations. Doubling n doubles the work: O(n).",
        ),
        (
            "Two separate loops each visit all n items. What is the total complexity?",
            ["O(n²)", "O(1)", "O(n)", "O(log n)"],
            2,
            "The loops run one after the other: n + n = 2n. Ignoring the constant factor gives O(n), not O(n²).",
        ),
    ),
    (
        "binary_search",
        "algorithms",
        "The power of cutting in half",
        0.35,
        ["complexity"],
        "A million possibilities. About twenty comparisons.",
        "Binary search works on sorted data. Compare the target with the middle value. If the target is larger, discard the left half; if smaller, discard the right half. Each unsuccessful comparison halves the remaining possibilities. After k halvings, n / 2ᵏ items remain. Reaching one item takes about log₂(n) halvings.",
        "Look for 13 in [1, 3, 5, 7, 9, 11, 13, 15]. Compare with 7: go right. Compare with 11: go right. Compare with 13: found. Sorting is essential; an unsorted list gives no safe half to discard.",
        "When each step halves the problem, logarithms count the steps.",
        r"\frac{n}{2^k}=1\quad\Rightarrow\quad k=\log_2 n",
        (
            "What is the worst-case time complexity of binary search on a sorted array?",
            ["O(1)", "O(log n)", "O(n)", "O(n²)"],
            1,
            "Each comparison removes about half the candidates, so the number of comparisons grows logarithmically.",
        ),
        (
            "A sorted array grows from 1,024 to 2,048 items. Roughly how many extra comparisons does binary search need?",
            ["1", "10", "1,024", "Twice as many"],
            0,
            "Doubling the array adds one halving step: log₂(2048) − log₂(1024) = 11 − 10 = 1.",
        ),
    ),
    (
        "recursion",
        "programming",
        "A smaller version of the same problem",
        0.3,
        [],
        "A function can solve a problem by asking itself a smaller question.",
        "Recursion breaks a problem into a smaller instance of itself. It needs a base case that returns directly and a recursive case that moves toward it. Each call waits for the next one on the call stack. Without progress toward the base case, calls continue until the stack or another resource is exhausted.",
        "factorial(4) = 4 × factorial(3), then 3 × factorial(2), then 2 × factorial(1). The base case factorial(1) = 1 lets the answers unwind: 2, 6, 24.",
        "Every recursive solution needs a stopping rule and measurable progress toward it.",
        r"n!=n(n-1)!\,,\qquad 0!=1",
        (
            "What makes a recursive function stop?",
            ["Calling itself", "A reachable base case", "A large input", "Using a loop"],
            1,
            "The base case returns without another recursive call, and the recursive cases must eventually reach it.",
        ),
        (
            "f(n) returns f(n + 1) for positive n and stops only at n = 0. What happens for f(3)?",
            ["Returns 0", "Returns 3", "Never reaches its base case", "Runs once"],
            2,
            "The input increases away from zero, so the base case is unreachable from 3.",
        ),
    ),
    (
        "hash_tables",
        "programming",
        "A shortcut from keys to values",
        0.4,
        ["complexity"],
        "How can a dictionary find one word without reading every word?",
        "A hash table computes a hash from a key and uses it to choose a bucket. With a good hash function and controlled load, lookups take expected O(1) time. Different keys can land in the same bucket: a collision. Chaining or probing resolves collisions. Worst-case lookup can be O(n), so constant time is an average-case claim.",
        "A contacts app hashes a name to pick a bucket. If Ana and Eli share a bucket, it compares the original keys within that bucket. The hash narrows the search; it does not prove the keys are equal.",
        "A hash narrows the search; collision handling preserves correctness.",
        None,
        (
            "Two different keys produce the same bucket index. This is called…",
            ["Recursion", "A collision", "Sorting", "A base case"],
            1,
            "A collision happens when distinct keys map to the same bucket. The table must resolve it.",
        ),
        (
            "Every key lands in one chained bucket. What can lookup degrade to?",
            ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
            2,
            "You may need to scan all n keys in the bucket. Expected constant time depends on a reasonable distribution.",
        ),
    ),
    (
        "merge_sort",
        "algorithms",
        "Split. Sort. Reunite.",
        0.5,
        ["complexity", "recursion"],
        "Two sorted lists are surprisingly easy to combine.",
        "Merge sort splits a list in half until each piece has at most one item. It merges sorted pieces by repeatedly taking the smaller front item. Each level processes O(n) items, and balanced splitting creates O(log n) levels. Together these give O(n log n) time. A typical array implementation uses O(n) auxiliary memory.",
        "Merge [2, 8] and [3, 5]: take 2, then 3, then 5, then 8. Each front comparison produces one output, so merging two lists with n total items takes O(n) time.",
        "Linear work at each of logarithmically many levels gives O(n log n).",
        r"T(n)=2T(n/2)+O(n)=O(n\log n)",
        (
            "Why does merge sort have a log n factor?",
            [
                "Every comparison is logarithmic",
                "There are logarithmically many splitting levels",
                "It uses a hash table",
                "Only one item is visited",
            ],
            1,
            "Halving the input repeatedly creates about log₂(n) levels; merging across each level is linear.",
        ),
        (
            "How much time does it take to merge two sorted lists with n total elements?",
            ["O(1)", "O(log n)", "O(n)", "O(n²)"],
            2,
            "Each element is read and written a bounded number of times, so merging is linear.",
        ),
    ),
    (
        "graphs",
        "algorithms",
        "A language for connections",
        0.3,
        [],
        "Friendships, roads, and dependencies share the same skeleton.",
        "A graph consists of vertices and edges. Vertices represent entities; edges represent connections. Directed edges have a direction, like a prerequisite pointing to a course. Undirected edges work both ways, like a two-way road. An adjacency list stores each vertex's neighbors efficiently for sparse graphs.",
        "For roads A–B, A–C, and C–D, the neighbors of A are B and C. A path A → C → D connects A to D in two edges. A weighted graph can attach a travel time to each road.",
        "Choose what vertices and edges mean before choosing a graph algorithm.",
        None,
        (
            "In a road-network graph, cities are usually represented by…",
            ["Vertices", "Weights only", "Loops", "Arrays only"],
            0,
            "Vertices represent the entities, in this case cities. Edges represent roads connecting them.",
        ),
        (
            "A course A is required before B, but B is not required before A. Which edge fits?",
            ["An undirected A–B edge", "A directed A → B edge", "No edge", "A self-loop on B"],
            1,
            "Prerequisites are directional relationships. A → B expresses the required order.",
        ),
    ),
    (
        "bfs",
        "algorithms",
        "Explore one layer at a time",
        0.5,
        ["graphs"],
        "The shortest route in an unweighted graph comes from patiently exploring nearby options first.",
        "Breadth-first search uses a queue. Start with one vertex, visit its unvisited neighbors, then their neighbors. Mark a vertex visited when you enqueue it to avoid duplicate work. Because BFS explores by edge distance, the first discovery of a vertex gives a shortest path in an unweighted graph. Complexity with adjacency lists is O(V + E).",
        "If A connects to B and C, and B connects to D, the queue explores A, then B and C, then D. D is two edges from A. A weighted graph can require Dijkstra's algorithm instead.",
        "A queue makes exploration expand in distance layers.",
        r"T=O(V+E)",
        (
            "Which data structure drives breadth-first search?",
            ["A stack", "A queue", "A sorted array", "A single counter"],
            1,
            "A first-in, first-out queue explores earlier, closer discoveries before later, farther ones.",
        ),
        (
            "Does BFS always find the minimum-cost path when edges have different positive weights?",
            [
                "Yes, always",
                "Only if vertices are sorted",
                "No; edge count and cost can differ",
                "Only in directed graphs",
            ],
            2,
            "BFS minimizes the number of edges. A route with fewer edges may still have greater total weight.",
        ),
    ),
    (
        "dynamic_programming",
        "algorithms",
        "Remember work you've already done",
        0.65,
        ["recursion"],
        "Sometimes the fastest computation is the one you don't repeat.",
        "Dynamic programming reuses solutions to overlapping subproblems. Memoization caches results in a recursive solution; tabulation builds results from smaller states upward. Choose a state, define a recurrence, specify base cases, and decide an evaluation order. Not every recursive problem has enough overlap to benefit.",
        "Naive Fibonacci recomputes fib(3) many times. Storing fib(k) means each of n states is computed once. With constant work per state, time becomes O(n); keeping just the last two numbers uses O(1) auxiliary space for an iterative version.",
        "Identify the state and reuse repeated subproblems.",
        r"F_n=F_{n-1}+F_{n-2},\quad F_0=0,\ F_1=1",
        (
            "What does memoization store?",
            [
                "Random inputs",
                "Results of subproblems already solved",
                "Only the final answer",
                "All possible programs",
            ],
            1,
            "Memoization caches solved states so later calls can reuse their answers.",
        ),
        (
            "There are n distinct states and each takes constant work after dependencies are solved. Total time?",
            ["O(1)", "O(log n)", "O(n)", "O(2ⁿ)"],
            2,
            "Compute each of n states once, spending O(1) per state: O(n) total.",
        ),
    ),
    (
        "logarithms",
        "foundations",
        "Logarithms count the multiplications",
        0.25,
        [],
        "How many times must you double 1 to reach 32?",
        "A logarithm asks which exponent produces a number. log₂(32) = 5 because 2⁵ = 32. It can also count how many times a quantity can be halved to reach 1. Logarithms turn multiplication into addition, which is why they appear in growth, information, and algorithm analysis. Real logarithms require positive inputs and a positive base other than 1.",
        "Start at 1: 2, 4, 8, 16, 32. Five doublings. Starting from 32 and halving also takes five steps: 16, 8, 4, 2, 1.",
        "A logarithm is an exponent seen from the other direction.",
        r"\log_b x=y\iff b^y=x",
        (
            "What is log₂(64)?",
            ["2", "6", "8", "32"],
            1,
            "2⁶ = 64, so the exponent needed to reach 64 from base 2 is 6.",
        ),
        (
            "If log₂(a) = 3 and log₂(b) = 4, what is log₂(ab)?",
            ["1", "7", "12", "64"],
            1,
            "The product rule gives log₂(ab) = log₂(a) + log₂(b) = 3 + 4 = 7.",
        ),
    ),
    (
        "vectors",
        "linear_algebra",
        "Numbers with a direction",
        0.2,
        [],
        "A vector tells you how far to go—and which way.",
        "A vector is an ordered collection of components. In two dimensions, (3, 2) can describe moving 3 units right and 2 units up. It has magnitude and direction. Geometrically, moving the arrow without changing its length or direction represents the same vector. Its magnitude comes from the Pythagorean theorem.",
        "A displacement of (3, 4) travels 3 units east and 4 north. Its straight-line length is √(3² + 4²) = 5 units, not 7. The 7-unit route follows the two sides of a triangle.",
        "Components describe independent directions; magnitude combines them.",
        r"\|\mathbf v\|=\sqrt{v_x^2+v_y^2}",
        (
            "What is the magnitude of the vector (3, 4)?",
            ["1", "5", "7", "12"],
            1,
            "By the Pythagorean theorem, √(3² + 4²) = √25 = 5.",
        ),
        (
            "Which vector points in the same direction as (2, 1) and is twice as long?",
            ["(2, 2)", "(4, 2)", "(1, 2)", "(−2, −1)"],
            1,
            "Multiply both components by the positive scalar 2: (4, 2).",
        ),
    ),
    (
        "vector_operations",
        "linear_algebra",
        "Add movements, component by component",
        0.3,
        ["vectors"],
        "Two journeys can become one arrow.",
        "Add vectors by adding corresponding components. Geometrically, place the second arrow's tail at the first arrow's tip. The sum runs from the first tail to the second tip. Multiplying by a scalar scales every component; a negative scalar also reverses direction. Vector subtraction adds the reversed second vector.",
        "Walk (2, 1), then (1, 3). Your total displacement is (3, 4). To undo the trip, move (−3, −4). The order of these displacements does not change the final position.",
        "Add corresponding coordinates; use arrows to see why it works.",
        r"(a,b)+(c,d)=(a+c,b+d)",
        (
            "What is (2, 3) + (4, −1)?",
            ["(6, 2)", "(8, −3)", "(2, 4)", "(6, 4)"],
            0,
            "Add the x components: 2 + 4 = 6. Add the y components: 3 + (−1) = 2.",
        ),
        (
            "What is −2 × (3, −1)?",
            ["(−6, 2)", "(6, −2)", "(1, −3)", "(−6, −2)"],
            0,
            "Multiply each component by −2. A negative scalar reverses the direction and scales the length.",
        ),
    ),
    (
        "dot_product",
        "linear_algebra",
        "How much do two vectors agree?",
        0.4,
        ["vector_operations"],
        "The dot product measures alignment.",
        "Multiply corresponding components, then add them. The result is a scalar. Geometrically, a · b = |a||b| cos θ. A positive result means an acute angle, zero means perpendicular nonzero vectors, and a negative result means an obtuse angle. The zero vector also has zero dot product with every vector.",
        "For (2, 1) and (3, 4), the dot product is 2×3 + 1×4 = 10. For (1, 0) and (0, 1), it is zero: the coordinate axes are perpendicular.",
        "The sign reveals alignment; the size also depends on both lengths.",
        r"\mathbf a\cdot\mathbf b=\sum_i a_i b_i=\|a\|\|b\|\cos\theta",
        (
            "What is (1, 2) · (3, 4)?",
            ["(3, 8)", "7", "11", "24"],
            2,
            "Multiply and add: 1×3 + 2×4 = 3 + 8 = 11. The result is a scalar.",
        ),
        (
            "Two nonzero vectors have a negative dot product. Their angle is…",
            ["Exactly 0°", "Acute", "Exactly 90°", "Obtuse"],
            3,
            "Their magnitudes are positive, so a negative dot product implies cos θ < 0, hence an obtuse angle.",
        ),
    ),
    (
        "matrices",
        "linear_algebra",
        "A matrix is a machine for vectors",
        0.3,
        ["vectors"],
        "A grid of numbers can describe an entire transformation.",
        "A matrix arranges numbers into rows and columns. An m × n matrix has m rows and n columns. Multiplying it by a vector with n components yields a vector with m components. Each output component is a row's dot product with the input. A square identity matrix leaves vectors unchanged.",
        "The matrix [[2, 0], [0, 3]] sends (x, y) to (2x, 3y). It stretches horizontal distances by 2 and vertical distances by 3. It sends (1, 2) to (2, 6).",
        "Matrix columns tell you where the input basis vectors go.",
        r"\begin{bmatrix}2&0\\0&3\end{bmatrix}\begin{bmatrix}x\\y\end{bmatrix}=\begin{bmatrix}2x\\3y\end{bmatrix}",
        (
            "A 3 × 2 matrix has…",
            ["2 rows and 3 columns", "3 rows and 2 columns", "6 rows", "Only diagonal entries"],
            1,
            "Matrix shape is written rows × columns: 3 rows and 2 columns.",
        ),
        (
            "What does the 2 × 2 identity matrix do to (5, −2)?",
            ["Returns (0, 0)", "Returns (−5, 2)", "Returns (5, −2)", "Returns (2, 5)"],
            2,
            "The identity transformation leaves every vector unchanged.",
        ),
    ),
    (
        "matrix_multiplication",
        "linear_algebra",
        "Combine two transformations",
        0.5,
        ["matrices", "dot_product"],
        "Matrix multiplication composes actions, so order matters.",
        "To multiply A of shape m × n by B of shape n × p, take each row of A dotted with each column of B. The result has shape m × p. With column vectors, AB applies B first, then A. In general AB is not BA, because rotating then stretching can differ from stretching then rotating.",
        "If A doubles horizontal coordinates and B rotates by 90°, applying B then A to (1, 0) gives (0, 1). Applying A then B gives (0, 2). This is why switching the order can change the result.",
        "Inner dimensions must match; the rightmost transformation acts first.",
        r"(AB)_{ij}=\sum_k A_{ik}B_{kj}",
        (
            "A is 2 × 3 and B is 3 × 4. What shape is AB?",
            ["2 × 4", "3 × 3", "4 × 2", "Not defined"],
            0,
            "The inner dimensions 3 match; the outer dimensions give 2 × 4.",
        ),
        (
            "For a column vector v, which transformation acts first in ABv?",
            ["A", "B", "Both simultaneously", "Neither"],
            1,
            "ABv = A(Bv), so B acts on v first, followed by A.",
        ),
    ),
    (
        "linear_transformations",
        "linear_algebra",
        "A transformation that respects addition",
        0.55,
        ["matrix_multiplication"],
        "Straight grid lines stay straight—and the origin stays put.",
        "A linear transformation respects vector addition and scalar multiplication: T(au + bv) = aT(u) + bT(v). Its behavior is completely determined by its action on basis vectors. Rotations, shears, and scalings around the origin are linear. A nonzero translation is affine, not linear, because it moves the zero vector.",
        "T(x, y) = (x + 2y, y) is a shear. It sends (1, 0) to (1, 0) and (0, 1) to (2, 1). These images become the columns of its matrix [[1, 2], [0, 1]].",
        "Know where the basis goes, and you know where every vector goes.",
        r"T(a\mathbf u+b\mathbf v)=aT(\mathbf u)+bT(\mathbf v)",
        (
            "Which operation is NOT a linear transformation on ordinary 2D vectors?",
            [
                "Rotation around the origin",
                "Scaling by 2",
                "Translation by (1, 1)",
                "Reflection across the x-axis",
            ],
            2,
            "A nonzero translation moves the origin, whereas every linear transformation must send zero to zero.",
        ),
        (
            "T(1,0) = (2,0) and T(0,1) = (1,3). For linear T, what is T(1,1)?",
            ["(2,3)", "(3,3)", "(1,1)", "(2,0)"],
            1,
            "Linearity gives T(1,1) = T(1,0) + T(0,1) = (3,3).",
        ),
    ),
    (
        "eigenvectors",
        "linear_algebra",
        "Directions that stay on their line",
        0.7,
        ["linear_transformations"],
        "Some vectors survive a transformation with only their scale changed.",
        "An eigenvector is a nonzero vector v for which Av = λv. The matrix can stretch, shrink, reverse, or collapse it, but the result stays on its span. The scalar λ is the eigenvalue. The zero vector is excluded because it satisfies the equation for every λ and reveals no special direction.",
        "For A = [[2, 0], [0, 3]], the vector (1, 0) is an eigenvector with eigenvalue 2, and (0, 1) has eigenvalue 3. The vector (1, 1) becomes (2, 3), which is not a scalar multiple of (1, 1).",
        "Eigenvectors reveal invariant directions; eigenvalues describe their scaling.",
        r"A\mathbf v=\lambda\mathbf v,\qquad\mathbf v\ne\mathbf 0",
        (
            "If Av = 3v for nonzero v, the eigenvalue is…",
            ["v", "A", "0", "3"],
            3,
            "The eigenvalue is the scalar multiplying v: λ = 3.",
        ),
        (
            "An eigenvector has eigenvalue −2. What happens under the transformation?",
            [
                "It rotates by 90°",
                "It reverses direction and doubles in length",
                "It becomes zero",
                "It stays unchanged",
            ],
            1,
            "Multiplying by −2 reverses direction and doubles the magnitude, while staying on the same line.",
        ),
    ),
    (
        "probability",
        "probability",
        "A number for uncertainty",
        0.2,
        [],
        "Probability describes what could happen across possible outcomes.",
        "A probability lies between 0 and 1. Zero means impossible within the model, and one means certain. For equally likely finite outcomes, divide favorable outcomes by total outcomes. The probabilities of an event and its complement sum to 1. An outcome's probability is not a promise about the very next trial.",
        "A fair six-sided die has three even faces: 2, 4, 6. P(even) = 3/6 = 1/2. Rolling odd several times does not force the next independent roll to be even.",
        "Check whether outcomes are equally likely before counting them.",
        r"P(A^c)=1-P(A)",
        (
            "What is the probability of rolling a number greater than 4 on a fair six-sided die?",
            ["1/6", "1/3", "1/2", "2/3"],
            1,
            "Two outcomes, 5 and 6, qualify out of six equally likely outcomes: 2/6 = 1/3.",
        ),
        (
            "A fair coin lands heads five times in a row. Probability of heads on the next independent toss?",
            ["0", "1/6", "1/2", "1"],
            2,
            "Independence means earlier outcomes do not alter the next toss's probability: it remains 1/2.",
        ),
    ),
    (
        "conditional_probability",
        "probability",
        "New information changes the sample space",
        0.4,
        ["probability"],
        "Knowing one thing can change the odds of another.",
        "Conditional probability P(A|B) asks how likely A is once B is known. Restrict attention to outcomes in B, then find the fraction also in A. The formula is P(A∩B)/P(B), provided P(B) is positive. P(A|B) generally differs from P(B|A).",
        "A fair die is rolled. You know it is even, so the possible results are now {2, 4, 6}. The probability it is greater than 3 is 2/3, because {4, 6} qualify.",
        "Conditioning narrows the outcomes you should consider.",
        r"P(A\mid B)=\frac{P(A\cap B)}{P(B)}",
        (
            "A fair die is even. What is the probability it shows 6?",
            ["1/6", "1/3", "1/2", "2/3"],
            1,
            "Given even, the equally likely possibilities are 2, 4, and 6. One of the three is 6.",
        ),
        (
            "Are P(rain | clouds) and P(clouds | rain) necessarily equal?",
            ["Yes", "Only at night", "No", "Both are always 1"],
            2,
            "The conditions define different sample spaces. Reversing a conditional probability is generally invalid.",
        ),
    ),
    (
        "bayes",
        "probability",
        "Update a belief with evidence",
        0.55,
        ["conditional_probability"],
        "Evidence matters. So does how plausible the idea was before it arrived.",
        "Bayes' rule combines a prior probability with the likelihood of evidence under a hypothesis. The denominator normalizes across all ways the evidence could arise. Strong-looking evidence can still leave a rare hypothesis unlikely if false positives are common among the many alternatives.",
        "Of 1,000 messages, 100 are spam. A filter flags 90 of those plus 90 of the 900 legitimate messages. Among the 180 flagged messages, 90 are spam: a 50% chance, despite detecting 90% of spam.",
        "Reason in natural frequencies when conditional probabilities get confusing.",
        r"P(H\mid E)=\frac{P(E\mid H)P(H)}{P(E)}",
        (
            "In the example, 90 spam and 90 legitimate messages are flagged. What fraction of flagged messages are spam?",
            ["10%", "50%", "90%", "100%"],
            1,
            "There are 180 flagged messages in total. Of those, 90 are spam, so 90/180 = 1/2.",
        ),
        (
            "Before seeing new evidence, your probability for a hypothesis is called the…",
            ["Posterior", "Likelihood", "Prior", "Complement"],
            2,
            "The prior describes belief before the evidence. Updating with the evidence produces the posterior.",
        ),
    ),
    (
        "derivatives",
        "calculus",
        "How fast is this changing, right now?",
        0.4,
        [],
        "Average speed describes a trip. A derivative describes a moment.",
        "A derivative is the limit of an average rate of change as the interval shrinks toward zero, when that limit exists. Geometrically it is the slope of the tangent line. A positive derivative means local increase; a negative one means local decrease. A zero derivative alone does not guarantee a maximum or minimum.",
        "For position s(t) = t², average speed from t = 3 to t = 3 + h is ((3+h)² − 9)/h = 6 + h. As h tends to zero, instantaneous speed tends to 6.",
        "Shrink the interval to turn average change into instantaneous change.",
        r"f'(x)=\lim_{h\to0}\frac{f(x+h)-f(x)}{h}",
        (
            "If f(x) = x², what is f′(3)?",
            ["3", "6", "9", "12"],
            1,
            "The derivative of x² is 2x. At x = 3, the slope is 6.",
        ),
        (
            "Does f′(a) = 0 guarantee a local maximum or minimum?",
            ["Yes", "No; x³ at x=0 is a counterexample", "Only if a=0", "It guarantees a maximum"],
            1,
            "x³ has derivative zero at 0 but keeps increasing through it. A zero derivative is not sufficient.",
        ),
    ),
]

VISUALS = {
    "binary_search": {
        "type": "array_elimination",
        "values": [1, 3, 5, 7, 9, 11, 13, 15],
        "labels": [],
        "caption": "Find 13. Each comparison discards a half.",
    },
    "vectors": {
        "type": "vector",
        "values": [3, 4],
        "labels": [],
        "caption": "Move the sliders. Watch the components and length change.",
    },
    "logarithms": {
        "type": "growth",
        "values": [],
        "labels": [],
        "caption": "Compare n with log₂(n) as the input grows.",
    },
    "complexity": {
        "type": "growth",
        "values": [],
        "labels": [],
        "caption": "Linear work grows faster than logarithmic work.",
    },
    "recursion": {
        "type": "steps",
        "values": [],
        "labels": ["factorial(4)", "4 × factorial(3)", "4 × 3 × factorial(2)", "4 × 3 × 2 × 1 = 24"],
        "caption": "Follow the calls to the base case, then combine their results.",
    },
    "merge_sort": {
        "type": "steps",
        "values": [],
        "labels": [
            "[8, 2, 5, 3]",
            "[8, 2]  |  [5, 3]",
            "[8] [2] [5] [3]",
            "[2, 8]  |  [3, 5]",
            "[2, 3, 5, 8]",
        ],
        "caption": "Split into smaller lists, then merge in order.",
    },
}


def seed_database(db: Session) -> None:
    if db.scalar(select(Subject.id).limit(1)):
        return
    db.add_all(
        [
            Subject(id="cs", name="Computer Science", color="mint"),
            Subject(id="math", name="Mathematics", color="lavender"),
        ]
    )
    db.flush()
    for ident, subject, name in [
        ("algorithms", "cs", "Algorithms"),
        ("programming", "cs", "Programming"),
        ("foundations", "math", "Foundations"),
        ("linear_algebra", "math", "Linear algebra"),
        ("probability", "math", "Probability"),
        ("calculus", "math", "Calculus"),
    ]:
        db.add(Topic(id=ident, subject_id=subject, name=name))
    db.flush()
    for row in CURRICULUM:
        cid, topic, title, difficulty, _, _, explanation, *_ = row
        db.add(Concept(id=cid, topic_id=topic, name=title, summary=explanation, difficulty=difficulty))
    db.flush()
    for row in CURRICULUM:
        cid, _, title, difficulty, parents, hook, explanation, example, takeaway, equation, q1, q2 = row
        db.add(Mastery(concept_id=cid))
        for parent in parents:
            db.add(ConceptDependency(concept_id=cid, prerequisite_id=parent))
        for kind in [
            "micro_lesson",
            "quiz",
            "flashcard",
            "visualization" if cid in VISUALS else "example",
            "challenge",
        ]:
            quiz = q2 if kind == "challenge" else q1
            is_question = kind in ("quiz", "challenge")
            card = CardData.model_validate(
                dict(
                    concept_id=cid,
                    type=kind,
                    title=(
                        "Put it to work: "
                        if kind == "challenge"
                        else "Quick recall: "
                        if kind == "quiz"
                        else "In practice: "
                        if kind == "example"
                        else "Remember: "
                        if kind == "flashcard"
                        else "See it: "
                        if kind == "visualization"
                        else ""
                    )
                    + title,
                    hook=quiz[0] if kind == "flashcard" else hook,
                    explanation=example if kind == "example" else explanation,
                    takeaway=takeaway,
                    difficulty=min(0.95, difficulty + (0.1 if kind == "challenge" else 0)),
                    estimated_seconds=30
                    if kind in ("quiz", "flashcard")
                    else 60
                    if kind == "challenge"
                    else 45,
                    steps=[example] if kind in ("micro_lesson", "visualization") else [],
                    equation=equation,
                    code="def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)"
                    if cid == "recursion" and kind == "micro_lesson"
                    else None,
                    visualization=VISUALS.get(cid) if kind in ("micro_lesson", "visualization") else None,
                    quiz={"question": quiz[0], "answers": quiz[1], "correct": quiz[2], "explanation": quiz[3]}
                    if is_question
                    else None,
                )
            )
            store_card(db, card, "seed")
    db.add_all(
        [
            LearningPath(
                id="algorithms",
                subject_id="cs",
                title="Think like an algorithm",
                description="From counting operations to finding elegant solutions.",
                concept_ids=[
                    "complexity",
                    "binary_search",
                    "recursion",
                    "hash_tables",
                    "merge_sort",
                    "graphs",
                    "bfs",
                    "dynamic_programming",
                ],
            ),
            LearningPath(
                id="linear-algebra",
                subject_id="math",
                title="See linear algebra",
                description="Build a geometric intuition, one transformation at a time.",
                concept_ids=[
                    "vectors",
                    "vector_operations",
                    "dot_product",
                    "matrices",
                    "matrix_multiplication",
                    "linear_transformations",
                    "eigenvectors",
                ],
            ),
            LearningPath(
                id="uncertainty",
                subject_id="math",
                title="Make sense of uncertainty",
                description="From a roll of the dice to updating beliefs with evidence.",
                concept_ids=["probability", "conditional_probability", "bayes"],
            ),
            LearningPath(
                id="change",
                subject_id="math",
                title="The mathematics of change",
                description="Explore growth, scales, and instantaneous change.",
                concept_ids=["logarithms", "derivatives"],
            ),
        ]
    )
    db.commit()
