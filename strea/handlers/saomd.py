import copy
import random
from typing import List, NamedTuple, Optional, Tuple

from discord import Message

from sqlalchemy.orm.exc import NoResultFound

from ..box import box
from ..command import PM, argument, only
from ..models.saomd import (
    COST_TYPE_LABEL,
    CostType,
    Player,
    PlayerScout,
    Scout,
    ScoutType,
    Step,
)
from ..util import bold, fuzzy_korean_ratio, strike

THREE_STAR_CHARACTERS: List[str] = [
    '[검은 스프리건] 키리토',
    '[고독한 공략조] 키리토',
    '[검사] 클라인',
    '[불요정 사무라이] 클라인',
    '스메라기',
    '[혈맹 기사단 단장] 히스클리프',
    '붉은 눈의 자자',
    '크라딜',
    '유진',
    '[자유분방한 땅요정] 스트레아',
    '[컨버트 성공] 사치',
    '[공략의 화신] 아스나',
    '[싸우는 대장장이 요정] 리즈벳',
    '[아이템 마스터] 레인',
    '룩스',
    '[중간층의 아이돌] 시리카',
    '[신속한 정보상] 아르고',
    '[고양이 요정의 정보] 아르고',
    '[강인한 방어자] 에길',
    '[수수께끼의 여전사] 유우키',
    '[명장을 목표로] 리즈벳',
    '[총의 세계] 시논',
    '[고양이 궁사] 시논',
    '[날렵한 고양이 요정] 시리카',
    '[탐구하는 그림자 요정] 필리아',
    '사쿠야',
    '[바람의 마법사] 리파',
    '[어린 음악 요정] 세븐',
    '알리샤 루',
    '시우네',
]

TWO_STAR_CHARACTERS: List[str] = [
    '[전 베타 테스터] 키리토',
    '클라인',
    '디어벨',
    '코바츠',
    '싱커',
    '시구르드',
    '스트레아',
    '사치',
    '아스나',
    '요루코',
    '유리엘',
    '시리카',
    '필리아',
    '아르고',
    '사샤',
    '에길',
    '키바오',
    '카게무네',
    '리즈벳',
    '로자리아',
    '시논',
]

THREE_STAR_WEAPONS: List[str] = [
    '문릿 소드',
    '명장의 롱 소드',
    '홍염도',
    '아이스 블레이드',
    '명장의 롱 소드x2',
    '시밸릭 레이피어',
    '지룡의 스팅어',
    '브레이브 레이피어',
    '문라이트 쿠크리',
    '미세리코르데',
    '미드나이트 크리스',
    '바르바로이 메이스',
    '게일 자그널',
    '블러디 클럽',
    '화이트 슈터',
    '롱 레인지 배럿',
    '자이언트 스나이퍼',
    '시밸릭 보우',
    '페트라 보우',
    '팔콘 슈터',
    '에메랄드 로드',
    '타이들 로드',
    '결정의 마법 지팡이',
    '게일 할버드',
    '페트라 트윈스',
]

TWO_STAR_WEAPONS: List[str] = [
    '퀸즈 나이트소드',
    '브레이브 젬 소드',
    '바람이 깃든 칼',
    'Q 나이트 소드 x B 젬 소드',
    '플레임 레이피어',
    '미스릴 레이피어',
    '스트라이크  대거',
    '윈드 대거',
    '플레임 나이프',
    '워 픽',
    '아쿠아 메이스',
    '미스릴 메이스',
    '스텔스 라이플',
    '프리시전 라이플',
    '더블칼럼 매거진',
    '아쿠아 스프레드',
    '플레임 슈터',
    '다크 보우',
    '플레임 완드',
    '이블 완드',
    '에텔 스태프',
    '미스릴 스피어',
    '다크니스 글레이브',
]


class Weapon(NamedTuple):
    """NamedTuple to store saomd weapon"""

    name: str
    grade: str
    ratio: int
    category: str
    attribute: str
    attack: int
    critical: int
    battle_skills: Optional[List[str]]


def get_or_create_player(sess, user) -> Player:
    try:
        player = sess.query(Player).filter_by(user=user).one()
    except NoResultFound:
        player = Player()
        player.user = user
        with sess.begin():
            sess.add(player)
    return player


def get_similar_scout_by_title(sess, type: ScoutType, title: str) -> Scout:
    scouts = sess.query(Scout).filter_by(type=type).all()

    scout = scouts[0]
    ratio = fuzzy_korean_ratio(scout.title, title)
    for s in scouts[1:]:
        _ratio = fuzzy_korean_ratio(s.title, title)
        if ratio < _ratio:
            ratio = _ratio
            scout = s
    return scout


def get_or_create_player_scout(
    sess,
    player: Player,
    scout: Scout
) -> PlayerScout:
    try:
        player_scout = sess.query(PlayerScout).filter(
            PlayerScout.player == player,
            PlayerScout.scout == scout,
            ).one()
    except NoResultFound:
        first = sess.query(Step).filter(
            Step.scout == scout,
            Step.is_first == True,  # noqa
        ).one()
        player_scout = PlayerScout()
        player_scout.player = player
        player_scout.scout = scout
        player_scout.next_step = first

        with sess.begin():
            sess.add(player_scout)

    return player_scout


def choice_units(
    scout: Scout,
    step: Step,
    s3_units: List[str],
    s2_units: List[str],
    seed: int=None,
) -> List[Tuple[int, str]]:
    result = []
    result_length = step.count
    five = step.s5_chance
    four = five + step.s4_chance
    three = four + 0.25
    random.seed(seed)
    for x in range(step.s5_fixed):
        result.append((5, random.choice(scout.s5_units)))
        result_length -= 1
    for x in range(step.s4_fixed):
        result.append((4, random.choice(scout.s4_units)))
        result_length -= 1
    for x in range(result_length):
        r = random.random()
        if r <= five:
            result.append((5, random.choice(scout.s5_units)))
        elif r <= four:
            result.append((4, random.choice(scout.s4_units)))
        elif r <= three:
            result.append((3, random.choice(s3_units)))
        else:
            result.append((2, random.choice(s2_units)))

    if scout.type == ScoutType.character:
        result.sort(key=lambda x: -x[0])

    random.seed(None)

    return result


def get_record_crystal(scout: Scout, seed: int=None) -> int:
    record_crystal = 0

    if scout.record_crystal:
        cases: List[int] = []
        chances: List[float] = []
        random.seed(seed)
        for case, chance in scout.record_crystal:
            cases.append(case)
            chances.append(chance)
        record_crystal = random.choices(cases, chances)[0]
        random.seed(None)

    return record_crystal


def process_release_crystal_and_deck(
    player: Player,
    chars: List[Tuple[int, str]]
) -> Tuple[List[str], int]:
    results: List[str] = []
    release_crystal = 0
    characters = copy.deepcopy(player.characters)
    for c in chars:
        character = characters.get(c[1])
        if character:
            if c[0] == 5:
                if character['rarity'] == 5:
                    release_crystal += 100
                    results.append(f'★5 {strike(c[1])} → 해방결정 100개')
                else:
                    release_crystal += 50
                    character['rarity'] = 5
                    results.append(f'★4→5 {bold(c[1])} + 해방결정 50개')
            elif c[0] == 4:
                release_crystal += 50
                results.append(f'★4 {strike(c[1])} → 해방결정 50개')
            elif c[0] == 3:
                release_crystal += 2
                results.append(f'★3 {strike(c[1])} → 해방결정 2개')
            else:
                release_crystal += 1
                results.append(f'★2 {strike(c[1])} → 해방결정 1개')
        else:
            characters[c[1]] = {
                'rarity': c[0],
            }
            if c[0] in [4, 5]:
                results.append(f'★{c[0]} {bold(c[1])}')
            else:
                results.append(f'★{c[0]} {c[1]}')

    player.characters = characters
    player.release_crystal += release_crystal

    return results, release_crystal


def process_weapon_inventory(
    player: Player,
    weapons: List[Tuple[int, str]]
) -> List[str]:
    results: List[str] = []
    player_weapons = copy.deepcopy(player.weapons)
    for w in weapons:
        w0 = str(w[0])
        if w0 not in player_weapons:
            player_weapons[w0] = {}
        if w[1] in player_weapons[w0]:
            player_weapons[w0][w[1]]['count'] += 1
        else:
            player_weapons[w0][w[1]] = {
                'count': 1,
            }

        if w[0] in [4, 5]:
            results.append(f'★{w[0]} {bold(w[1])}')
        else:
            results.append(f'★{w[0]} {w[1]}')

    player.weapons = player_weapons

    return results


def process_step_cost(
    player: Player,
    scout: Scout,
    step: Step,
    record_crystal: int
):
    record_crystal_name = (
        f'{scout.title} {COST_TYPE_LABEL[CostType.record_crystal]}'
    )
    record_crystals = copy.deepcopy(player.record_crystals)
    if step.cost_type == CostType.diamond:
        player.used_diamond += step.cost

        if record_crystal:
            if record_crystal_name in player.record_crystals:
                record_crystals[record_crystal_name] += record_crystal
            else:
                record_crystals[record_crystal_name] = record_crystal
    elif step.cost_type == CostType.record_crystal:
        if record_crystal_name in player.record_crystals:
            record_crystals[record_crystal_name] += (
                record_crystal - step.cost
            )
        else:
            record_crystals[record_crystal_name] = (
                record_crystal - step.cost
            )

    player.record_crystals = record_crystals


@box.command('캐릭뽑기', ['캐뽑'], channels=only(
    'simulation', 'test', PM, error='시뮬레이션 채널에서만 해주세요'
))
@argument('title', nargs=-1, concat=True,
          count_error='스카우트 타이틀을 입력해주세요')
async def saomd_character_scout(bot, message: Message, sess, title: str):
    """
    소드 아트 온라인 메모리 디프래그의 캐릭터 뽑기를 시뮬레이팅합니다.

    `{PREFIX}캐뽑 두근두근` (두근두근 수증기와 미인의 온천 스카우트 11연차를 시뮬레이션)

    지원되는 스카우트 타이틀은 `{PREFIX}캐뽑종류` 로 확인하세요.

    """

    player = get_or_create_player(sess, message.author.id)
    scout = get_similar_scout_by_title(sess, ScoutType.character, title)
    player_scout = get_or_create_player_scout(sess, player, scout)

    step: Step = player_scout.next_step

    chars = choice_units(
        scout, step, THREE_STAR_CHARACTERS, TWO_STAR_CHARACTERS)
    record_crystal = get_record_crystal(scout)
    results, release_crystal = process_release_crystal_and_deck(player, chars)

    process_step_cost(player, scout, step, record_crystal)
    player_scout.next_step = step.next_step or step

    with sess.begin():
        sess.add(player)
        sess.add(player_scout)

    await bot.say(
        message.channel,
        ('{cost_type} {cost}개 써서 {title} {step} {count}{c}차를 해보자!'
         '\n\n{result}\n\n해방 결정이 {release_crystal}개'
         '{record_crystal} 생겼어!').format(
            cost_type=COST_TYPE_LABEL[step.cost_type],
            cost=step.cost,
            title=scout.title,
            step=step.name,
            count=step.count,
            c='연' if step.count > 1 else '단',
            result='\n'.join(results),
            release_crystal=release_crystal,
            record_crystal=(
                f', 기록결정 크리스탈이 {record_crystal}개'
                if record_crystal > 0 else ''
            ),
        )
    )


@box.command('무기뽑기', ['무뽑'], channels=only(
    'simulation', 'test', PM, error='시뮬레이션 채널에서만 해주세요'
))
@argument('title', nargs=-1, concat=True,
          count_error='스카우트 타이틀을 입력해주세요')
async def saomd_weapon_scout(bot, message: Message, sess, title: str):
    """
    소드 아트 온라인 메모리 디프래그의 무기 뽑기를 시뮬레이팅합니다.

    `{PREFIX}무뽑 두근두근` (두근두근 수증기와 미인의 온천 스카우트 11연차를 시뮬레이션)

    지원되는 스카우트 타이틀은 `{PREFIX}무뽑종류` 로 확인하세요.

    """

    player = get_or_create_player(sess, message.author.id)
    scout = get_similar_scout_by_title(sess, ScoutType.weapon, title)
    player_scout = get_or_create_player_scout(sess, player, scout)

    step: Step = player_scout.next_step

    weapons = choice_units(scout, step, THREE_STAR_WEAPONS, TWO_STAR_WEAPONS)
    record_crystal = get_record_crystal(scout)
    results = process_weapon_inventory(player, weapons)

    process_step_cost(player, scout, step, record_crystal)
    player_scout.next_step = step.next_step or step

    with sess.begin():
        sess.add(player)
        sess.add(player_scout)

    await bot.say(
        message.channel,
        ('{cost_type} {cost}개 써서 {title} {step} {count}{c}차를 해보자!'
         '\n\n{result}\n\n{record_crystal}').format(
            cost_type=COST_TYPE_LABEL[step.cost_type],
            cost=step.cost,
            title=scout.title,
            step=step.name,
            count=step.count,
            c='연' if step.count > 1 else '단',
            result='\n'.join(results),
            record_crystal=(
                f'기록결정 크리스탈이 {record_crystal}개 생겼어!'
                if record_crystal > 0 else ''
            ),
        )
    )


@box.command('시뮬결과리셋', channels=only(
    'simulation', 'test', PM, error='시뮬레이션 채널에서만 해주세요'
))
async def saomd_sim_result_reset(bot, message: Message, sess):
    """
    SAOMD 시뮬 결과 리셋

    `{PREFIX}시뮬결과리셋` (SAOMD 시뮬레이션 결과를 모두 삭제)

    """

    try:
        player = sess.query(Player).filter_by(user=message.author.id).one()
    except NoResultFound:
        await bot.say(
            message.channel,
            '리셋할 데이터가 없어!'
        )
        return

    sess.query(PlayerScout).filter_by(player=player).delete()

    player.record_crystals = {}
    player.weapons = {}
    player.characters = {}
    player.release_crystal = 0
    player.used_diamond = 0

    with sess.begin():
        sess.add(player)

    await bot.say(
        message.channel,
        '리셋했어!'
    )
