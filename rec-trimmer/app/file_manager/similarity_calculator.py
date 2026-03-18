from .interfaces import SimmilarityCalculator


__all__ = ['JaccardCalculator', 'LevenshteinCalculator',]


class JaccardCalculator(SimmilarityCalculator):
    def is_similar(
        self,
        first: str,
        second: str,
        similarity_threshold: float = 0.5
    ) -> bool:
        return self._jaccard_metric(first, second) >= similarity_threshold

    def _jaccard_metric(
        self,
        first: str,
        second: str
    ) -> float:
        first_words: set[str] = set(first.split())
        second_words: set[str] = set(second.split())

        set_union = first_words.union(second_words)
        set_intersection = first_words.intersection(second_words)

        return len(set_intersection) / len(set_union)


class LevenshteinCalculator(SimmilarityCalculator):
    def is_similar(
        self,
        first: str,
        second: str,
        similarity_threshold: float
    ) -> bool:
        longer = max(len(first), len(second))
        shorter = min(len(first), len(second))

        if shorter / longer < 0.4:
            return False

        simm_score: float = 1 - (self._levenshtein_distance(first, second) / longer)
        return simm_score >= similarity_threshold

    def _levenshtein_distance(self, first: str, second: str) -> int:
        n, m = len(first), len(second)

        if n > m:
            first, second = second, first
            n, m = m, n

        current = [0] * (n + 1)
        previous = list(range(n + 1))

        for i in range(1, m + 1):
            current[0] = i
            for j in range(1, n + 1):
                if first[j-1] == second[i-1]:
                    current[j] = previous[j-1]
                else:
                    current[j] = 1 + min(
                        previous[j],    # удаление
                        current[j-1],   # вставка
                        previous[j-1]   # замена
                    )
            previous, current = current, previous

        return previous[n]
