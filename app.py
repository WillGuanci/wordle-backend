from flask import Flask, request, jsonify
from flask_cors import CORS
from collections import Counter
from collections import defaultdict
import math

def calculate_entropy(candidate_words, remaining_words, valid_solutions=None):
    def get_feedback_pattern(guess, solution):
        pattern = ['b'] * 5
        used = [False] * 5

        # Green pass
        for i in range(5):
            if guess[i] == solution[i]:
                pattern[i] = 'g'
                used[i] = True

        # Yellow pass
        for i in range(5):
            if pattern[i] == 'b' and guess[i] in solution:
                for j in range(5):
                    if not used[j] and guess[i] == solution[j]:
                        pattern[i] = 'y'
                        used[j] = True
                        break

        return ''.join(pattern)

    entropy_scores = []

    for candidate in candidate_words:
        pattern_counts = defaultdict(int)

        for actual in remaining_words:
            pattern = get_feedback_pattern(candidate, actual)
            pattern_counts[pattern] += 1

        total = sum(pattern_counts.values())
        entropy = 0
        for count in pattern_counts.values():
            p = count / total
            entropy += p * math.log2(1 / p)
        if VALID_SOLUTIONS and candidate in VALID_SOLUTIONS:
            entropy += 0.5  # adjust this value as needed
            print(f"Boosted entropy for {candidate}")
        entropy_scores.append((candidate, entropy))

    entropy_scores.sort(key=lambda x: x[1], reverse=True)
    return [word for word, score in entropy_scores[:20]]


app = Flask(__name__)
CORS(app)  # Allow requests from frontend

# Load the word list
with open('all_valid_guesses.txt') as f:
    ALL_WORDS = [line.strip() for line in f.readlines()]

with open('wordle-answers-alphabetical.txt') as f:
    VALID_SOLUTIONS = [line.strip() for line in f]
remaining_words = ALL_WORDS.copy()

def matches_feedback(word, guess, feedback):
    used = [False] * 5
    for i in range(5):
        if feedback[i] == 'g' and word[i] != guess[i]:
            return False
        if feedback[i] == 'g':
            used[i] = True
    for i in range(5):
        if feedback[i] == 'y':
            if guess[i] == word[i] or guess[i] not in word:
                return False
            indices = [j for j, c in enumerate(word) if c == guess[i] and not used[j]]
            if not indices:
                return False
            used[indices[0]] = True
        elif feedback[i] == 'b':
            g_or_y_count = sum(
                1 for j in range(5)
                if guess[j] == guess[i] and feedback[j] in 'gy'
            )
            if word.count(guess[i]) > g_or_y_count:
                return False
    return True

@app.route('/filter', methods=['POST'])
def filter_words():
    
    global remaining_words
    

    
    data = request.get_json()
    guess = data['guess'].lower()
    feedback = ''.join(data['feedback']).lower()


    # Step 1: Filter remaining words
    remaining_words = [w for w in remaining_words if matches_feedback(w, guess, feedback)]

    # Step 2: Score by letter frequency
    letter_counts = Counter()
    for word in remaining_words:
        letter_counts.update(set(word))  # only count unique letters per word

    def word_score(word):
        return sum(letter_counts[c] for c in set(word))

    # Step 3: Sort words by score (descending)
    ranked_words = calculate_entropy(remaining_words, VALID_SOLUTIONS, VALID_SOLUTIONS)

    return jsonify({'remaining': ranked_words[:20]})

@app.route('/reset', methods=['POST'])
def reset_words():
    global remaining_words, ALL_WORDS
    with open('all_valid_guesses.txt') as f:
        ALL_WORDS = [line.strip() for line in f.readlines()]

    remaining_words = ALL_WORDS.copy()
    return jsonify({'status': 'reset'})

if __name__ == '__main__':
    app.run(debug=True)
