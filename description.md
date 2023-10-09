# 仕様確認
## Roleに対する指示
`metagpt/roles/role.py`に`prompt`のテンプレートがある
### 1. PREFIX_TEMPLATE
ロールに対しての役割定義テンプレ。各ロール.py(例:`metagpt/roles/engineer.py`)で定義されている以下の情報を埋め込んで各ロール用の役割定義を行なっている。
- **name**: 名前(例: Alex)
- **profile**: 職業(例: Engineer)
- **goal**: 役割のゴール(例: Write elegant, readable, extensible, efficient code)
- **constraints**: 制約(例: The code should conform to standards like PEP8 and be modular and maintainable)

### 2. STATE_TEMPLATE
過去のroleとasistantの会話記録、roleが行うactionのリスト、過去のやり取りの中から何回目のやり取りを採用するのかなどを定義している。
- **history**: roleとasistantの会話記録
- **states**: roleが実行したactionが`[f"{idx}. {action}]"`のリスト形式で格納される。格納されたactionのいずれかが採用され、次のステップへ引き継がれる。(同じactionでもAto数回やり取りするので、リスト形式で保持し、そのうちどれを採用するのかを決める)
- **n_states**: 同一actionでroleとasistantが、やり取りを行ったかの回数。

### 3. ROLE_TEMPLATE
**※現在未使用**
roleに対して、現在何回目のやり取りなのか、過去に行ったやり取りに基づいた回答をするべきという指示を定義している。
- **state**: 何回目のやり取りなのか。(回数:int)
- **history**: roleとasistantの会話記録
- **name**: roleの名前
- **result**: asistantからの回答内容(response)

<hr>

## `startup.py`を実行した後のフロー
### 1 SoftwareCompanyを初期化
初期化時に以下の内部変数を定義している
- **environment**: 実行環境で共有されるMessageを格納できる。`Environment`は`metagpt/environment.py`で定義されている。各roleは`environment`に`Message`を発行でき、他の`role`によって監視が可能。`role`は監視したい`Message`を`self._watch([BossRequirement])`のように指定できる。監視している`Message`が`environment`に`push`されると'_init_actions'で設定したActionの実行が開始される。
- **investment**: 使用可能なOpenAI API の金額を定義。`default`は$10.0で初期化される。
- **idea**: アイディア。空白文字""で初期化される。後の処理で、コマンドライン実行時に`startup.py`の第一引数で指定した文字列が代入される。
### 2 hire: 仕様するroleをリストで定義（併せて各roleの初期化を行なっている）
※`Engineer`や`QaEngineer`の定義もここに含む</br>
以下のようにリスト形式で追加する。</br>
```python
company.hire(
    [
        ProductManager(),
        Architect(),
        ProjectManager(),
    ]
)
```
リストに追加したい場合は再度以下のようにリスト形式で追加する。
```python
company.hire([QaEngineer()])
```
### 3 invest: 使用可能なOpenAI API の金額を定義
※ここはあまり重要ではないので、細かい調査は後回し
### 4 start_project: idea(コマンド実行時に引数で指定した指示文言)を定義
内部でenviromentに対して`publish_message`としてrole="BOSS"のMessageを定義している。
#### 4.1 `publish_message`
`metagpt/schema.py`の`Message クラス`の仕様に則ったMessageを引数に渡すことで実行環境の`memory`と`history`にMessageを追加できる。
#### 4.2 `Message`
実行環境に対して要件や指示を定義する際の仕様。結構重要かも。
`software_company.py`の`start_project`関数での使用例と`metagpt/schema.py`の`Message クラス`引数の詳細は以下に記す。
##### 使用例
- **role**: roleを指定。`software_company.py`の`start_project`関数では`role`に**BOSS**が指定されている。
- **content**: コマンドライン実行時に指定された`idea`
- **cause_by**: Actionクラスを指定する。`BossRequirement`。`metagpt/actions/add_requirement.py`で定義されている。**細かい実装の詳細が記載されていないBossの要件指示**。

##### `metagpt/schema.py`の`Message クラス`引数
```python
content: str
instruct_content: BaseModel = field(default=None)
role: str = field(default='user')  # system / user / assistant
cause_by: Type["Action"] = field(default="")
sent_from: str = field(default="")
send_to: str = field(default="")
restricted_to: str = field(default="")
```

<hr>

## いったん整理
以下のような流れるになる。
```
1. SoftwareCompany初期化(company = SoftwareCompany())
    実行環境に`enviroment`が定義される。
2. SoftwareCompanyに各ロールを追加(company.hire([role]))
    ProductManager: BossRequirementを監視。WritePRDを実行。
    Architect: WritePRDを監視。WriteDesignを実行。
    ProjectManager: WriteDesignを監視。WriteTasksを実行。
    Engineer: WriteTasksを監視。WriteCode、WriteCodeReviewを実行。
    QaEngineer: WriteCode, WriteCodeReview, WriteTest, RunCode, DebugErrorを監視。WriteTestを実行。
3. SoftwareCompanyにinvestを設定(company.invest(investment))
4. SoftwareCompanyにideaを設定(company.start_project(idea))
    environmentにBossRequirementとしてidea(Message)が追加される
5. 各roleのタスクを実行(company.run(n_round=n_round))
    - BossRequirementを監視しているProductManagerがWritePRDを実行。WritePRDの結果がenvironmentに追加される。
    - WritePRDを監視しているArchitectがWriteDesignを実行。workspaceにdocs, resourcesディレクトリを作成。WriteDesignの結果を workspace/docs/prd.md と workspace/docs/system_design.md に出力。WriteDesignの結果がenvironmentに追加される。
    - WriteDesignを監視しているProjectManagerがWriteTasksを実行。WriteTasksの結果を workspace/requirements.txt と workspace/docs/api_spec_and_tasks.md に出力。WriteTasksの結果がenvironmentに追加される。
    - WriteTasksを監視しているEngineerが WriteDesign, WriteTasks の結果を取得。取得した内容をもとにWriteCodeを実行。取得した結果とWriteCodeの結果をもとにWriteCodeReviewを実行。(※WriteCodeReviewが有効になっていない場合はスキップ)WriteCode, WriteCodeReviewの結果をもとに workspace/workspace/filename.py にcodeを出力。WriteCode, WriteCodeReviewの結果がenvironmentに追加される。
    - WriteCode, WriteCodeReviewを監視しているQaEngineerがWriteTestを実行。WriteCodeで出力されたファイルを読み込み workspace/tests/filename.py にテストコードを出力。WriteTestの結果がenvironmentに追加される。
```
<hr>

`Engineer` クラス:
このクラスはエンジニアが行う基本的なタスクを実行します。具体的には、`use_code_review`フラグがTrueの場合、コードの生成（`WriteCode`）とコードのレビュー（`WriteCodeReview`）の両方が実行されます。
最終的に生成したコードはファイルに書き出されます。


`QaEngineer` クラス:
このクラスはQAエンジニアが行う基本的なタスクを実行します：
- コードが書かれたらそのコードのテストを書きます。
- テストが書かれたらテストを実行します。
- コードを実行したら、エラーをデバッグし、バグ修正を行います。


`startup`関数:
この関数は他の役割（`ProductManager`、`Architect`、`ProjectManager`）とともに、`Engineer`と`QaEngineer`を雇います。
- `code_review`や`implement`フラグが`True`の場合には`Engineer`を雇い、コードレビューを数回行うことができます。これは、`Engineer`クラスの`use_code_review`オプションで制御されます。
`Engineer`は具体的な実装（コーディング）を行います。
- `run_tests`フラグが`True`の場合には`QaEngineer`を雇います。`QaEngineer`はテストを作成・実行し、バグを検出します。
`company.run(n_round=n_round)`を実行すると、それぞれのロール（役割）がするべき行動を実行します（エンジニアはコードを書き、QAエンジニアはテストを実行し、etc.）。これらの行動は`timestep`または`round`で制御され、指定したラウンド数だけ繰り返されます。
