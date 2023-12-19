import csv
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt

folder = ''
file1 = ''
file2 = ''

with open(f'{folder}/{file1}.csv', mode='r') as file:
    reader = csv.reader(file)
    ff1_features = [np.array(row, dtype=np.float32) for row in reader]

with open(f'{folder}/{file2}.csv', mode='r') as file:
    reader = csv.reader(file)
    ff2_features = [np.array(row, dtype=np.float32) for row in reader]

max_similarity = -1
min_similarity = float('inf')
total_similarity = 0
num_comparisons = 0
similarity_above_80_count = 0
similarity_counts = defaultdict(int)

num_vectors = min(len(ff1_features), len(ff2_features))

for i in range(num_vectors):
    similarity = np.dot(ff1_features[i], ff2_features[i]) / (np.linalg.norm(ff1_features[i]) * np.linalg.norm(ff2_features[i]))
    
    max_similarity = max(max_similarity, similarity)
    min_similarity = min(min_similarity, similarity)
    
    total_similarity += similarity
    num_comparisons += 1
    
    similarity_percent = int(similarity * 100)
    similarity_counts[similarity_percent] += 1
    
    if similarity >= 0.8:
        similarity_above_80_count += 1
        print(f'Similarity between vector {i} in ff1 and vector {i} in ff2: {similarity_percent}%')

print(f'Maximum similarity: {max_similarity * 100}%')
print(f'Minimum similarity: {min_similarity * 100}%')

if num_comparisons > 0:
    average_similarity = (total_similarity / num_comparisons) * 100
    print(f'Average similarity: {average_similarity}%')
else:
    print('No comparisons made.')

similarity_above_80_percent = (similarity_above_80_count / num_comparisons) * 100
print(f'Percentage of similarities greater than or equal to 80%: {similarity_above_80_percent}%')

sorted_counts = sorted(similarity_counts.items(), key=lambda x: x[1], reverse=True)
for similarity, count in sorted_counts:
    print(f'Number of similarities at {similarity}%: {count}')

sorted_counts = sorted(similarity_counts.items(), key=lambda x: x[0])
similarities = [similarity for similarity, count in sorted_counts]
counts = [count for similarity, count in sorted_counts]

plt.figure(figsize=(10, 6))
plt.bar(similarities, counts, width=0.5, align='center')
plt.xlabel('Similarity Percentage')
plt.ylabel('Count')
plt.title('Distribution of Similarity Percentages')
plt.xticks(similarities, rotation=90)
plt.tight_layout()
plt.show()
