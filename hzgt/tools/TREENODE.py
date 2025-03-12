# -*- coding: utf-8 -*-

from typing import List, Optional
from ..Decorator import vargs

class TreeNode:
    """
    二叉树节点类

    属性:

    - val (int): 节点存储的值
    - left (TreeNode): 指向左子节点的引用
    - right (TreeNode): 指向右子节点的引用
    """
    def __init__(self, x):
        self.val = x
        self.left = None
        self.right = None


class BinaryTreeTraverser:
    """
    二叉树遍历类
    """
    def __init__(self, nodes: List[Optional[int]]):
        """
        初始化二叉树遍历器

        :param nodes: 包含节点值的列表, 其中None表示空节点
        """
        self.root = self._buildtree(nodes)

    def _buildtree(self, nodes, index=0) -> Optional[TreeNode]:
        """
        递归构建二叉树

        :param nodes: 包含节点值的列表
        :param index: 当前节点在 `node` 列表中的索引
        :return: node: 构建的二叉树根节点. 如果索引超出范围或节点值为 None. 则返回 None
        """
        if index >= len(nodes) or nodes[index] is None:
            return None
        node = TreeNode(nodes[index])
        node.left = self._buildtree(nodes, 2 * index + 1)
        node.right = self._buildtree(nodes, 2 * index + 2)
        return node

    def LDR(self) -> List[int]:  # 中序遍历
        """
        中序遍历

        :return: list: 中序遍历的节点值列表
        """
        return self._traverse('LDR', self.root)

    def DLR(self) -> List[int]:  # 前序遍历
        """
        前序遍历

        :return: list: 前序遍历的节点值列表
        """
        return self._traverse('DLR', self.root)

    def LRD(self) -> List[int]:  # 后序遍历
        """
        后序遍历

        :return: list: 后序遍历的节点值列表
        """
        return self._traverse('LRD', self.root)

    @vargs({"order": {'LDR', 'DLR', 'LRD'}})
    def _traverse(self, order: str, node: TreeNode):
        """
        :param order: str 遍历顺序，支持'LDR'、'DLR'和'LRD'
        :param node: TreeNode 当前遍历的节点
        :return: list: 按照给定顺序遍历的节点值列表
        """
        if not node:
            return []
        if order == 'LDR':
            return self._traverse('LDR', node.left) + [node.val] + self._traverse('LDR', node.right)
        elif order == 'DLR':
            return [node.val] + self._traverse('DLR', node.left) + self._traverse('DLR', node.right)
        elif order == 'LRD':
            return self._traverse('LRD', node.left) + self._traverse('LRD', node.right) + [node.val]
        else:
            raise ValueError(f'未知的遍历次序: {order}')
        
        
if __name__ == "__main__":
    # 使用Travel类
    a = BinaryTreeTraverser([i for i in range(1, 10)])

    print(a.LDR())  # 中序遍历结果
    print(a.DLR())  # 前序遍历结果
    print(a.LRD())  # 后序遍历结果
