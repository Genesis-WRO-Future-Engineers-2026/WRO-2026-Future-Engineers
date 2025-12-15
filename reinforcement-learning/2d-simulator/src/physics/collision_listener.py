"""Box2D衝突検出リスナー"""

from Box2D import b2ContactListener


class CollisionListener(b2ContactListener):
    """車両と壁の衝突を検出するContactListener"""

    def __init__(self):
        """
        ContactListenerを初期化

        Note:
            - collision_detected: 衝突が検出されたかのフラグ
            - 各ステップ開始時にリセットする必要がある
        """
        b2ContactListener.__init__(self)
        self.collision_detected = False

    def BeginContact(self, contact):
        """
        2つのfixtureが接触を開始した時に呼ばれる

        Args:
            contact: b2Contact オブジェクト

        Note:
            - contact.fixtureA, contact.fixtureBで接触した2つのfixtureを取得
            - fixture.body.userDataで各bodyの識別子を取得
            - 車両("vehicle")と壁("wall")の接触を検出
        """
        fixture_a = contact.fixtureA
        fixture_b = contact.fixtureB

        body_a = fixture_a.body
        body_b = fixture_b.body

        # userDataで車両と壁を識別
        user_data_a = body_a.userData
        user_data_b = body_b.userData

        # 車両と壁の衝突を検出
        if (user_data_a == "vehicle" and user_data_b == "wall") or \
           (user_data_a == "wall" and user_data_b == "vehicle"):
            self.collision_detected = True

    def EndContact(self, contact):
        """
        2つのfixtureの接触が終了した時に呼ばれる

        Args:
            contact: b2Contact オブジェクト

        Note:
            現在の実装では使用しないが、将来的な拡張のために定義
        """
        pass

    def reset(self):
        """
        衝突フラグをリセット

        Note:
            各ステップまたはエピソード開始時に呼び出す
        """
        self.collision_detected = False

    def is_collision(self) -> bool:
        """
        衝突が検出されたかを返す

        Returns:
            衝突が検出された場合True
        """
        return self.collision_detected
