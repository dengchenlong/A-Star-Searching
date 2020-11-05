import os
from pygame import *
import pygame as pg
import heapq
# from queue import Queue
from pygame.compat import geterror
from typing import List, Tuple

# 检查pygame
if not pg.font:
    print("Warning, fonts disabled")

#  定义全局变量
main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, "data")
have_source = False
have_dest = False
is_searching = False
start_block: 'Block'
goal_block: 'Block'
HEIGHT = 6
WIDTH = 13
SIZE = 96


def load_image(name, colorkey=None):
    fullname = os.path.join(data_dir, name)
    try:
        my_image = pg.image.load(fullname)
        # image = pg.transform.smoothscale(image, (SIZE - 1, SIZE - 1))
    except pg.error:
        print("Cannot load image:", fullname)
        raise SystemExit(str(geterror()))
    my_image = my_image.convert()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = my_image.get_at((0, 0))
        my_image.set_colorkey(colorkey, pg.RLEACCEL)
    return my_image


# left_button = False
# right_button = False


# 方块类
# noinspection DuplicatedCode
class Block(pg.sprite.Sprite):
    def __init__(self, n: int):
        pg.sprite.Sprite.__init__(self)  # call Sprite initializer
        self.location = (n % WIDTH, n // WIDTH)  # 位置
        self.image = load_image("空.png")
        self.rect = self.image.get_rect(topleft=(self.location[0] * SIZE, self.location[1] * SIZE))
        self.type = 0  # 0：空；1：障碍；2：起点；3：终点
        self.direction_came_from = None  # 0：空；1：上；2：下；3：左；4：右；13：左上；14：右上；23：左下；24：右上
        self.heuristic = None
        self.cost_so_far = None
        self.priority = None
        self.came_from_block = None
        self.neighbors = []

    def __lt__(self, rhs: "Block"):
        if self.location[0] < rhs.location[0]:
            return True
        elif self.location[0] > rhs.location[0]:
            return False
        else:
            if self.location[1] < rhs.location[1]:
                return True
            elif self.location[1] >= rhs.location[1]:
                return False

    def update(self):
        global have_source
        global have_dest
        if self.type == 0:
            self.image.blit(load_image("空.png"), (0, 0))
        elif self.type == 1:
            self.image.blit(load_image("障碍.png"), (0, 0))
        elif self.type == 2:
            self.image.blit(load_image("起点.png"), (0, 0))
        elif self.type == 3:
            self.image.blit(load_image("终点.png"), (0, 0))
        if self.direction_came_from is not None:
            if self.direction_came_from == 1:
                self.image.blit(load_image("下.png", -1), (0, 0))
            elif self.direction_came_from == 2:
                self.image.blit(load_image("上.png", -1), (0, 0))
            elif self.direction_came_from == 3:
                self.image.blit(load_image("右.png", -1), (0, 0))
            elif self.direction_came_from == 4:
                self.image.blit(load_image("左.png", -1), (0, 0))
            elif self.direction_came_from == 13:
                self.image.blit(load_image("右下.png", -1), (0, 0))
            elif self.direction_came_from == 14:
                self.image.blit(load_image("左下.png", -1), (0, 0))
            elif self.direction_came_from == 23:
                self.image.blit(load_image("右上.png", -1), (0, 0))
            elif self.direction_came_from == 24:
                self.image.blit(load_image("左上.png", -1), (0, 0))
        if self.priority is not None:
            my_font = pg.font.Font(None, 24)
            text = my_font.render("f:" + str(self.priority), True, (10, 10, 10))
            text_pos = text.get_rect(midbottom=(self.rect.centerx - self.rect.left, self.rect.bottom - self.rect.top))
            self.image.blit(text, text_pos)
        if self.cost_so_far is not None and self != start_block:
            my_font = pg.font.Font(None, 24)
            text = my_font.render("g:" + str(self.cost_so_far), True, (10, 10, 10))
            text_pos = text.get_rect(topleft=(5, 5))
            self.image.blit(text, text_pos)
        if self.heuristic is not None:
            my_font = pg.font.Font(None, 24)
            text = my_font.render("h:" + str(self.heuristic), True, (10, 10, 10))
            text_pos = text.get_rect(topright=(
                self.rect.topright[0] - self.rect.topleft[0] - 5, self.rect.topright[1] - self.rect.topleft[1] + 5))
            self.image.blit(text, text_pos)

    # 改变方块类型
    def change_type(self):
        global have_source
        global have_dest
        global start_block
        global goal_block
        if is_searching:
            if self.priority is None:
                if self.type == 0 or self.type == 1:
                    self.type = (self.type + 1) % 2
        else:
            if not (have_source or have_dest):
                self.type = (self.type + 1) % 4
                if self.type == 2:
                    have_source = True
                    start_block = self
            elif have_source and have_dest:
                if self.type == 0 or self.type == 1:
                    self.type = (self.type + 1) % 2
                elif self.type == 2:
                    self.type = 0
                    have_source = False
                    start_block = None
                elif self.type == 3:
                    self.type = 0
                    have_dest = False
                    goal_block = None
            elif have_source:
                self.type = (self.type + 1) % 4
                if self.type == 2:
                    self.type = (self.type + 1) % 4
                    have_dest = True
                    goal_block = self
                elif self.type == 3:
                    have_source = False
                    have_dest = True
                    start_block = None
                    goal_block = self
            else:
                self.type = (self.type + 1) % 4
                if self.type == 3:
                    self.type = (self.type + 1) % 4
                elif self.type == 2:
                    have_source = True
                    start_block = self
                elif self.type == 0:
                    have_dest = False
                    goal_block = None
        if self.type == 0:
            self.image.blit(load_image("空.png"), (0, 0))
        elif self.type == 1:
            self.image.blit(load_image("障碍.png"), (0, 0))
        elif self.type == 2:
            self.image.blit(load_image("起点.png"), (0, 0))
        elif self.type == 3:
            self.image.blit(load_image("终点.png"), (0, 0))

    # 更新父节点
    def came_from(self, a: 'Block'):
        self.came_from_block = a
        (x1, y1) = self.location
        (x2, y2) = a.location
        x = x2 - x1
        y = y2 - y1
        if x == 1 and y == 1:
            self.direction_came_from = 24
        elif x == 1 and y == 0:
            self.direction_came_from = 4
        elif x == 1 and y == -1:
            self.direction_came_from = 14
        elif x == 0 and y == 1:
            self.direction_came_from = 2
        elif x == 0 and y == -1:
            self.direction_came_from = 1
        elif x == -1 and y == 1:
            self.direction_came_from = 23
        elif x == -1 and y == 0:
            self.direction_came_from = 3
        elif x == -1 and y == -1:
            self.direction_came_from = 13

    def can_walk_neighbor(self, a: "Block") -> bool:
        if a.type == 1:
            return False
        # 不能从墙角过
        (x1, y1) = self.location
        (x2, y2) = a.location
        x = x2 - x1
        y = y2 - y1
        if abs(x) == 1 and abs(y) == 1:
            if all_blocks[self.location[0] + self.location[1] * WIDTH + x].type == 1:
                return False
            if all_blocks[self.location[0] + self.location[1] * WIDTH + y * WIDTH].type == 1:
                return False
        return True


# 计算估计开销
def heuristic(a: Block, b: Block) -> int:
    (x1, y1) = a.location
    (x2, y2) = b.location
    x = abs(x1 - x2)
    y = abs(y1 - y2)
    mini = min(x, y)
    maxi = max(x, y)
    return mini * 14 + (maxi - mini) * 10


# 计算开销
def cost(a: Block, b: Block) -> int:
    (x1, y1) = a.location
    (x2, y2) = b.location
    x = abs(x1 - x2)
    y = abs(y1 - y2)
    if x == 1 and y == 1:
        return 14
    else:
        return 10


class PriorityQueue:
    def __init__(self):
        self.elements: List[Tuple[int, Block]] = []

    def empty(self) -> bool:
        return len(self.elements) == 0

    def put(self, item: Block, priority: int):
        heapq.heappush(self.elements, (priority, item))

    def get(self) -> Block:
        return heapq.heappop(self.elements)[1]


open_list = PriorityQueue()
all_blocks: List[Block] = []
current: Block


def a_star_search_step():
    global open_list
    global is_searching
    global current

    if not open_list.empty():
        current = open_list.get()

        if current == goal_block:
            is_searching = False
            return

        for next_block in [a for a in current.neighbors if current.can_walk_neighbor(a)]:
            new_cost = current.cost_so_far + cost(current, next_block)
            if next_block.cost_so_far is None or new_cost < next_block.cost_so_far:
                next_block.cost_so_far = new_cost
                next_block.heuristic = heuristic(next_block, goal_block)
                next_block.priority = next_block.cost_so_far + next_block.heuristic
                next_block.came_from(current)
                open_list.put(next_block, next_block.priority)


def main():
    # 初始化界面
    global is_searching
    global start_block
    global goal_block
    global open_list
    global all_blocks
    global current
    pg.init()
    screen = pg.display.set_mode((SIZE * WIDTH - 1, SIZE * HEIGHT - 1))
    pg.display.set_caption("A*寻路")
    # 创建背景surface
    background = pg.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))
    screen.blit(background, (0, 0))
    # 写规则
    rect_screen = screen.get_rect()
    my_font = pg.font.Font("C:/Windows/Fonts/simhei.ttf", rect_screen.bottom // 10)
    text = my_font.render("操作说明：", True, (240, 240, 240))
    text_pos = text.get_rect(centerx=rect_screen.centerx)
    screen.blit(text, text_pos)
    text = my_font.render("鼠标点击设置方块样式：", True, (240, 240, 240))
    text_pos = text.get_rect(top=rect_screen.bottom // 9 * 1, centerx=rect_screen.centerx)
    screen.blit(text, text_pos)
    text = my_font.render("      蓝色起点 ", True, (0, 0, 255))
    text_pos = text.get_rect(top=rect_screen.bottom // 9 * 2, left=text_pos.left)
    screen.blit(text, text_pos)
    text = my_font.render("      绿色终点 ", True, (0, 255, 0))
    text_pos = text.get_rect(top=rect_screen.bottom // 9 * 3, left=text_pos.left)
    screen.blit(text, text_pos)
    text = my_font.render("      灰色障碍 ", True, (100, 100, 100))
    text_pos = text.get_rect(top=rect_screen.bottom // 9 * 4, left=text_pos.left)
    screen.blit(text, text_pos)
    text = my_font.render("空格分步搜索", True, (240, 240, 240))
    text_pos = text.get_rect(top=rect_screen.bottom // 9 * 5, left=text_pos.left)
    screen.blit(text, text_pos)
    text = my_font.render("回车一步搜索", True, (240, 240, 240))
    text_pos = text.get_rect(top=rect_screen.bottom // 9 * 6, left=text_pos.left)
    screen.blit(text, text_pos)
    text = my_font.render("任意键或点击屏幕继续", True, (240, 240, 240))
    text_pos = text.get_rect(top=rect_screen.bottom // 9 * 7, left=text_pos.left)
    screen.blit(text, text_pos)
    text = my_font.render("ESC键或点击关闭退出", True, (240, 240, 240))
    text_pos = text.get_rect(top=rect_screen.bottom // 9 * 8, left=text_pos.left)
    screen.blit(text, text_pos)
    pg.display.flip()
    clock = pg.time.Clock()
    loop = True
    while loop:
        clock.tick(60)
        for my_event in pg.event.get():
            if my_event.type == pg.QUIT:
                pg.quit()
                return
            elif my_event.type == pg.KEYDOWN and my_event.key == pg.K_ESCAPE:
                pg.quit()
                return
            elif my_event.type == pg.KEYDOWN:
                loop = False
            elif my_event.type == pg.MOUSEBUTTONUP:
                loop = False
    # 准备游戏环境
    all_blocks = []
    for i in range(WIDTH * HEIGHT):
        all_blocks.append(Block(i))
    # 保存相邻方块
    for i in range(WIDTH * HEIGHT):
        if i % WIDTH > 0:
            all_blocks[i].neighbors.append(all_blocks[i - 1])
        if i % WIDTH < WIDTH - 1:
            all_blocks[i].neighbors.append(all_blocks[i + 1])
        if i >= WIDTH:
            all_blocks[i].neighbors.append(all_blocks[i - WIDTH])
        if i <= WIDTH * (HEIGHT - 1) - 1:
            all_blocks[i].neighbors.append(all_blocks[i + WIDTH])
        if i >= WIDTH and i % WIDTH > 0:
            all_blocks[i].neighbors.append(all_blocks[i - WIDTH - 1])
        if i >= WIDTH and i % WIDTH < WIDTH - 1:
            all_blocks[i].neighbors.append(all_blocks[i - WIDTH + 1])
        if i <= WIDTH * (HEIGHT - 1) - 1 and i % WIDTH > 0:
            all_blocks[i].neighbors.append(all_blocks[i + WIDTH - 1])
        if i <= WIDTH * (HEIGHT - 1) - 1 and i % WIDTH < WIDTH - 1:
            all_blocks[i].neighbors.append(all_blocks[i + WIDTH + 1])
    all_sprites = pg.sprite.RenderPlain(all_blocks)
    # 主循环
    entire = False  # 是否分步
    loop = True
    while loop:
        clock.tick(60)

        # 处理输入事件
        for my_event in pg.event.get():
            if my_event.type == pg.QUIT:
                loop = False
            elif my_event.type == pg.KEYDOWN and my_event.key == pg.K_ESCAPE:
                loop = False
            elif my_event.type == pg.MOUSEBUTTONUP:
                pos = pg.mouse.get_pos()
                all_blocks[pos[0] // SIZE + pos[1] // SIZE * WIDTH].change_type()
            elif my_event.type == pg.KEYDOWN and my_event.key == pg.K_SPACE:
                if start_block is not None and goal_block is not None:
                    is_searching = True
                    loop = False
                    open_list.put(start_block, 0)
                    start_block.came_from = None
                    start_block.cost_so_far = 0
                    a_star_search_step()
            elif my_event.type == pg.KEYDOWN and my_event.key == pg.K_RETURN:
                if start_block is not None and goal_block is not None:
                    is_searching = True
                    loop = False
                    open_list.put(start_block, 0)
                    start_block.came_from = None
                    start_block.cost_so_far = 0
                    entire = True

        all_sprites.update()

        # 绘制界面
        screen.blit(background, (0, 0))
        all_sprites.draw(screen)
        pg.display.update()

    while is_searching:
        clock.tick(60)
        if entire:
            a_star_search_step()
        else:
            # 处理输入事件
            for my_event in pg.event.get():
                if my_event.type == pg.QUIT:
                    is_searching = False
                elif my_event.type == pg.KEYDOWN and my_event.key == pg.K_ESCAPE:
                    is_searching = False
                elif my_event.type == pg.MOUSEBUTTONUP:
                    pos = pg.mouse.get_pos()
                    all_blocks[pos[0] // SIZE + pos[1] // SIZE * WIDTH].change_type()
                elif my_event.type == pg.KEYDOWN and my_event.key == pg.K_SPACE:
                    a_star_search_step()
                elif my_event.type == pg.KEYDOWN and my_event.key == pg.K_RETURN:
                    entire = True

        all_sprites.update()

        # 绘制界面
        screen.blit(background, (0, 0))
        current.image.fill((200, 200, 200), special_flags=BLEND_MULT)
        all_sprites.draw(screen)
        pg.display.update()

    temp: Block = goal_block.came_from_block
    # 绘制结果
    while temp != start_block:
        temp.image.fill((255, 255, 0), special_flags=BLEND_MULT)
        temp = temp.came_from_block
    screen.blit(background, (0, 0))
    all_sprites.draw(screen)
    pg.display.update()

    loop = True
    while loop:
        clock.tick(60)
        # 处理输入事件
        for my_event in pg.event.get():
            if my_event.type == pg.QUIT:
                loop = False
            elif my_event.type == KEYDOWN:
                loop = False
            elif my_event.type == MOUSEBUTTONUP:
                loop = False

    pg.quit()


if __name__ == "__main__":
    main()
