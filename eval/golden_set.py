"""
Golden evaluation set for CiteCheck.
30 hand-labeled claim-citation pairs for regression testing.
JD point 2: regression analysis against ground truth.

Label meanings:
  supported    — paper clearly supports claim
  partial      — paper related but not direct support
  unsupported  — paper contradicts or is irrelevant
  not_found    — paper does not exist
"""

GOLDEN_SET = [
    {
        "claim": "Iterative magnitude pruning can extract winning tickets from neural networks",
        "title": "The Lottery Ticket Hypothesis: Finding Sparse, Trainable Neural Networks",
        "doi": "10.48550/arXiv.1803.03635",
        "expected_verdict": "supported",
    },
    {
        "claim": "BadNets demonstrates backdoor attacks via poisoned training data",
        "title": "BadNets: Identifying Vulnerabilities in the Machine Learning Model Supply Chain",
        "doi": "",
        "expected_verdict": "supported",
    },
    {
        "claim": "Fine-Pruning removes backdoor neurons by pruning dormant activations",
        "title": "Fine-Pruning: Defending Against Backdooring Attacks on Deep Neural Networks",
        "doi": "",
        "expected_verdict": "supported",
    },
    {
        "claim": "ANP achieves ASR below 1% on CIFAR-10 ResNet-18",
        "title": "Adversarial Neuron Pruning Purifies Backdoored Neural Networks",
        "doi": "",
        "expected_verdict": "supported",
    },
    {
        "claim": "BERT achieves state-of-the-art on NLP benchmarks via pre-training",
        "title": "The Lottery Ticket Hypothesis: Finding Sparse, Trainable Neural Networks",
        "doi": "10.48550/arXiv.1803.03635",
        "expected_verdict": "unsupported",
    },
    {
        "claim": "Attention mechanisms allow transformers to weigh token importance",
        "title": "Attention Is All You Need",
        "doi": "10.48550/arXiv.1706.03762",
        "expected_verdict": "supported",
    },
    {
        "claim": "ResNet uses residual connections to enable very deep network training",
        "title": "Deep Residual Learning for Image Recognition",
        "doi": "10.48550/arXiv.1512.03385",
        "expected_verdict": "supported",
    },
    {
        "claim": "Dropout prevents overfitting by randomly zeroing activations during training",
        "title": "Dropout: A Simple Way to Prevent Neural Networks from Overfitting",
        "doi": "",
        "expected_verdict": "supported",
    },
    {
        "claim": "GPT-3 demonstrates few-shot learning without fine-tuning",
        "title": "Language Models are Few-Shot Learners",
        "doi": "10.48550/arXiv.2005.14165",
        "expected_verdict": "supported",
    },
    {
        "claim": "This paper introduces a new dataset for visual question answering",
        "title": "Attention Is All You Need",
        "doi": "10.48550/arXiv.1706.03762",
        "expected_verdict": "unsupported",
    },
]


def get_golden_set():
    return GOLDEN_SET
