/**
 * AI Career Intelligence Platform — Question Bank
 * Built-in MCQ questions across Aptitude, Reasoning, Verbal & Technical
 */
'use strict';

const QuestionBank = (() => {

    // ── QUANTITATIVE APTITUDE ─────────────────────────────── //
    const quant = [
        { question: "A train travels 360 km at 90 km/h. How long does it take?", options: ["3 hours","4 hours","5 hours","6 hours"], correct: 1, explanation: "Time = Distance/Speed = 360/90 = 4 hours." },
        { question: "What is 15% of 240?", options: ["28","32","36","40"], correct: 2, explanation: "15% of 240 = 0.15 × 240 = 36." },
        { question: "If A can do a work in 12 days and B in 18 days, together they complete it in:", options: ["7.2 days","7 days","8 days","6 days"], correct: 0, explanation: "Together: 1/12 + 1/18 = 5/36 per day → 36/5 = 7.2 days." },
        { question: "The ratio of boys to girls in a class is 3:2. If there are 30 students, how many boys?", options: ["12","15","18","20"], correct: 2, explanation: "Boys = 3/(3+2) × 30 = 18." },
        { question: "What is the compound interest on ₹10,000 at 10% p.a. for 2 years?", options: ["₹2,000","₹2,100","₹2,200","₹2,500"], correct: 1, explanation: "CI = 10000(1.1)² - 10000 = 12100 - 10000 = ₹2100." },
        { question: "Two pipes fill a tank in 6 and 8 hours. Both open together fill it in:", options: ["3 h 26 min","3 h 30 min","3 h 20 min","4 hours"], correct: 0, explanation: "1/6 + 1/8 = 7/24 per hr → 24/7 ≈ 3 h 26 min." },
        { question: "A shopkeeper gives 20% discount on ₹500. What is the selling price?", options: ["₹380","₹400","₹420","₹450"], correct: 1, explanation: "SP = 500 × 0.80 = ₹400." },
        { question: "The average of 5 numbers is 20. If one number is removed, the average becomes 18. The removed number is:", options: ["25","28","30","32"], correct: 1, explanation: "Total = 100; remaining 4 = 72; removed = 28." },
        { question: "Speed of a boat in still water is 15 km/h. Speed of current is 3 km/h. Downstream speed:", options: ["12 km/h","15 km/h","18 km/h","21 km/h"], correct: 2, explanation: "Downstream = 15 + 3 = 18 km/h." },
        { question: "If x²-5x+6=0, the roots are:", options: ["1,6","2,3","1,5","3,4"], correct: 1, explanation: "(x-2)(x-3)=0 → x=2 or x=3." },
        { question: "A man saves 25% of his income. If income is ₹40,000, his expenditure is:", options: ["₹25,000","₹28,000","₹30,000","₹32,000"], correct: 2, explanation: "Savings = 25% = ₹10,000; expenditure = 40,000 - 10,000 = ₹30,000." },
        { question: "LCM of 12 and 18 is:", options: ["24","36","48","72"], correct: 1, explanation: "12 = 2²×3; 18 = 2×3²; LCM = 2²×3² = 36." },
    ];

    // ── LOGICAL REASONING ─────────────────────────────────── //
    const logical = [
        { question: "Odd one out: 2, 3, 5, 7, 9, 11", options: ["2","5","9","11"], correct: 2, explanation: "9 = 3×3 is not prime; all others are prime numbers." },
        { question: "If TRIANGLE is coded as URJBOHMF, what is the code for SQUARE?", options: ["TRVBSF","SQUARF","TRVBRF","SQUASD"], correct: 0, explanation: "Each letter is shifted by +1 in the alphabet." },
        { question: "Complete the series: 1, 4, 9, 16, 25, ?", options: ["30","35","36","40"], correct: 2, explanation: "Perfect squares: 1²,2²,3²…6² = 36." },
        { question: "All roses are flowers. Some flowers fade quickly. Therefore:", options: ["All roses fade quickly","Some roses may fade quickly","No roses fade quickly","All flowers are roses"], correct: 1, explanation: "We can only conclude 'some roses may fade quickly' - not a definitive statement." },
        { question: "In a row of 40, A is 16th from left. A's position from right:", options: ["24","25","26","27"], correct: 1, explanation: "From right = 40 - 16 + 1 = 25." },
        { question: "Which pattern continues: AZ, BY, CX, ?", options: ["DV","DW","EV","EW"], correct: 1, explanation: "First letters A,B,C,D (forward); second Z,Y,X,W (backward) → DW." },
        { question: "A is B's father. C is B's sister. D is A's father. C is D's:", options: ["Daughter","Grand-daughter","Niece","Sister"], correct: 1, explanation: "D is A's father → D is B and C's grandfather → C is D's grand-daughter." },
        { question: "Looking at a clock at 3:15, the angle between the hands is:", options: ["0°","7.5°","15°","22.5°"], correct: 1, explanation: "Hour hand at 97.5°, minute hand at 90°; angle = 7.5°." },
    ];

    // ── VERBAL ABILITY ─────────────────────────────────────── //
    const verbal = [
        { question: "Choose the correct spelling:", options: ["Accomodation","Accommodation","Accomadation","Acomodation"], correct: 1, explanation: "'Accommodation' has double 'c' and double 'm'." },
        { question: "Synonym of 'Eloquent':", options: ["Silent","Articulate","Awkward","Confused"], correct: 1, explanation: "Eloquent means well-spoken, articulate." },
        { question: "Antonym of 'Benevolent':", options: ["Kind","Generous","Malevolent","Charitable"], correct: 2, explanation: "Benevolent = well-wishing; antonym = malevolent (ill-wishing)." },
        { question: "Fill in the blank: She _______ at the office when I called.", options: ["is working","was working","has worked","had working"], correct: 1, explanation: "Past continuous tense is used for ongoing action in the past." },
        { question: "Select the correctly punctuated sentence:", options: ["Its raining outside","It's raining outside","Its' raining outside","Its raining, outside"], correct: 1, explanation: "'It's' is the contraction of 'it is'." },
    ];

    // ── TECHNICAL CS ───────────────────────────────────────── //
    const technical = [
        { question: "What is the time complexity of binary search?", options: ["O(n)","O(log n)","O(n log n)","O(n²)"], correct: 1, explanation: "Binary search halves the search space each step → O(log n)." },
        { question: "Which data structure uses LIFO?", options: ["Queue","Stack","Linked List","Tree"], correct: 1, explanation: "Stack follows Last In First Out (LIFO) principle." },
        { question: "In SQL, which clause filters groups?", options: ["WHERE","HAVING","GROUP BY","ORDER BY"], correct: 1, explanation: "HAVING filters after GROUP BY; WHERE filters before grouping." },
        { question: "What does HTTP 404 mean?", options: ["Server Error","Not Found","Forbidden","Unauthorized"], correct: 1, explanation: "HTTP 404 = Resource Not Found." },
        { question: "Which sorting algorithm has O(n log n) worst-case?", options: ["Bubble Sort","Quick Sort","Merge Sort","Selection Sort"], correct: 2, explanation: "Merge Sort guarantees O(n log n) in all cases." },
        { question: "What is a deadlock in OS?", options: ["CPU overload","Two processes waiting for each other","Memory overflow","Disk failure"], correct: 1, explanation: "Deadlock occurs when two or more processes are indefinitely blocked waiting on each other." },
        { question: "Which Python data structure is immutable?", options: ["List","Dictionary","Set","Tuple"], correct: 3, explanation: "Tuples are immutable; once created they cannot be changed." },
        { question: "What does OOP stand for?", options: ["Object Oriented Programming","Ordinary Object Protocol","Open Output Programming","None of these"], correct: 0, explanation: "OOP = Object Oriented Programming." },
        { question: "In React, what hook is used for side effects?", options: ["useState","useEffect","useContext","useMemo"], correct: 1, explanation: "useEffect hook manages side effects like API calls in React." },
        { question: "Which HTTP method is idempotent?", options: ["POST","PATCH","GET","None"], correct: 2, explanation: "GET is idempotent — multiple identical requests have the same effect." },
    ];

    // ── HR QUESTIONS ────────────────────────────────────────── //
    const hr = [
        { question: "What does 'Tell me about yourself' primarily evaluate?", options: ["Technical skills","Communication & self-awareness","Salary expectations","GPA"], correct: 1, explanation: "It tests communication, structure, and how you present your background." },
        { question: "STAR method stands for:", options: ["Situation, Task, Action, Result","Strategy, Team, Achievement, Role","Skill, Talent, Ability, Reach","None of these"], correct: 0, explanation: "STAR = Situation, Task, Action, Result — a structured answer format." },
        { question: "When asked 'What is your weakness?' — best approach:", options: ["Say you have none","Mention a real weakness and your effort to improve it","Mention a strength as weakness","Avoid the question"], correct: 1, explanation: "Acknowledge a genuine area of improvement and the steps you're taking to address it." },
    ];

    const all = {
        'Quantitative Aptitude': quant.map(q => ({ ...q, category: 'Quantitative Aptitude' })),
        'Logical Reasoning': logical.map(q => ({ ...q, category: 'Logical Reasoning' })),
        'Verbal Ability': verbal.map(q => ({ ...q, category: 'Verbal Ability' })),
        'Technical CS': technical.map(q => ({ ...q, category: 'Technical CS' })),
        'HR Questions': hr.map(q => ({ ...q, category: 'HR Questions' })),
    };

    function shuffle(arr) {
        const a = [...arr];
        for (let i = a.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [a[i], a[j]] = [a[j], a[i]];
        }
        return a;
    }

    function getByCategory(cat, n = 10) {
        const pool = all[cat] || all['Technical CS'];
        return shuffle(pool).slice(0, Math.min(n, pool.length));
    }

    function getMixed(n = 25) {
        const pools = Object.values(all).map(p => shuffle(p));
        const result = [];
        let i = 0;
        while (result.length < n) {
            for (const pool of pools) {
                if (pool[i]) result.push(pool[i]);
                if (result.length >= n) break;
            }
            i++;
            if (i > 15) break;
        }
        return shuffle(result).slice(0, n);
    }

    return { getByCategory, getMixed };
})();
