using UnityEngine;
using Unity.MLAgents;
using Unity.MLAgents.Actuators;
using Unity.MLAgents.Sensors;

public class CarAgent : Agent
{
    public Transform goal;
    public float moveSpeed = 5f;
    
    private Rigidbody rb;
    private Vector3 startPosition;

    public override void Initialize()
    {
        rb = GetComponent<Rigidbody>();
        startPosition = transform.localPosition;
    }

    public override void OnEpisodeBegin()
    {
        // 車をスタート位置に戻す
        transform.localPosition = startPosition;
        rb.linearVelocity = Vector3.zero;
        rb.angularVelocity = Vector3.zero;

        // ゴールをランダムな位置に
        goal.localPosition = new Vector3(
            Random.Range(-4f, 4f),
            0.5f,
            Random.Range(-4f, 4f)
        );
    }

    public override void CollectObservations(VectorSensor sensor)
    {
        // 車の位置（3）
        sensor.AddObservation(transform.localPosition);
        // ゴールの位置（3）
        sensor.AddObservation(goal.localPosition);
        // 車の速度（3）
        sensor.AddObservation(rb.linearVelocity);
    }

    public override void OnActionReceived(ActionBuffers actions)
    {
        // 行動を取得（前後、左右）
        float moveX = actions.ContinuousActions[0];
        float moveZ = actions.ContinuousActions[1];

        // 移動
        Vector3 move = new Vector3(moveX, 0, moveZ) * moveSpeed;
        rb.AddForce(move, ForceMode.VelocityChange);

        // ゴールに近づくと報酬
        float distanceToGoal = Vector3.Distance(transform.localPosition, goal.localPosition);
        
        // 小さな負の報酬（早くゴールに到達させる）
        AddReward(-0.001f);

        // ゴール到達
        if (distanceToGoal < 1.5f)
        {
            AddReward(1.0f);
            EndEpisode();
        }

        // 床から落ちた
        if (transform.localPosition.y < 0)
        {
            AddReward(-1.0f);
            EndEpisode();
        }
    }

    public override void Heuristic(in ActionBuffers actionsOut)
    {
        // 手動操作用（テスト用）
        var actions = actionsOut.ContinuousActions;
        actions[0] = Input.GetAxis("Horizontal");
        actions[1] = Input.GetAxis("Vertical");
    }
}