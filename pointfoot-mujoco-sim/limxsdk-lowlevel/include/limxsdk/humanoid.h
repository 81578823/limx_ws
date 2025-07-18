﻿/**
 * @file humanoid.h
 *
 * @brief This file contains the declarations of classes related to the control of humanoid robots.
 *
 * © [2025] LimX Dynamics Technology Co., Ltd. All rights reserved.
 */

#ifndef _LIMX_SDK_HUMANOID_H_
#define _LIMX_SDK_HUMANOID_H_

#include "limxsdk/macros.h"
#include "limxsdk/datatypes.h"
#include "limxsdk/apibase.h"

namespace limxsdk
{
  /**
   * @brief Class for controlling a humanoid robot using the LIMX SDK API.
   */
  class LIMX_SDK_API Humanoid : public ApiBase
  {
  public:
    /**
     * @brief Get an instance of the Humanoid class.
     * @return A pointer to a Humanoid instance (Singleton pattern).
     */
    static Humanoid *getInstance();

    /**
     * @brief Pure virtual initialization method.
     *        This method should specify the operations to be performed before using the object in the main function.
     * @param robot_ip_address The IP address of the robot.
     *                         For simulation, it is typically set to "127.0.0.1",
     *                         while for a real robot, it may be set to "10.192.1.2".
     * @return True if init successfully, otherwise false.
     */
    bool init(const std::string &robot_ip_address = "127.0.0.1") override;

    /**
     * @brief Get the number of motors in the robot.
     * @return The total number of motors.
     */
    uint32_t getMotorNumber() override;

    /**
     * @brief Override to obtain names of all robot motors.
     * Used for motor identification.
     * @return Vector of motor names; empty if unavailable.
     */
    std::vector<std::string> getMotorNames() override;

    /**
     * @brief Method to subscribe to updates of the robot's IMU (Inertial Measurement Unit) data.
     * @param cb The callback function to be invoked when new IMU data is received.
     */
    void subscribeImuData(std::function<void(const ImuDataConstPtr &)> cb) override;

    /**
     * @brief Subscribe to receive updates about the robot state.
     * The motor order for the state data is as follows:
     * Humanoid:
     *   0: left_hip_pitch_joint,   1: left_hip_roll_joint,   2: left_hip_yaw_joint  3: left_knee_joint  4: left_ankle_pitch_joint   5: left_ankle_roll_joint
     *   6: right_hip_pitch_joint,  7: right_hip_roll_joint,  8: right_hip_yaw_joint 9: right_knee_joint 10: right_ankle_pitch_joint 11: right_ankle_roll_joint
     *  12: waist_yaw_joint,       13: waist_roll_joint,     14: waist_pitch_joint,
     *  15: head_pitch_joint,      16: head_yaw_joint
     *  17: left_shoulder_pitch_joint,  18: left_shoulder_roll_joint,  19: left_shoulder_yaw_joint  20: left_elbow_joint
     *  21: left_hand_yaw_joint,  22: left_hand_roll_joint,  23: left_hand_pitch_joint
     *  24: right_shoulder_pitch_joint,  25: right_shoulder_roll_joint,  26: right_shoulder_yaw_joint,  27: right_elbow_joint
     *  28: right_hand_yaw_joint,  29: right_hand_roll_joint,  30: right_hand_pitch_joint
     *
     * @param cb The callback function to be invoked when a robot state update is received.
     */
    void subscribeRobotState(std::function<void(const RobotStateConstPtr &)> cb) override;

    /**
     * @brief Publish a command to control the robot's actions.
     * The motor order for the commnd data is as follows:
     * Humanoid:
     *   0: left_hip_pitch_joint,   1: left_hip_roll_joint,   2: left_hip_yaw_joint  3: left_knee_joint  4: left_ankle_pitch_joint   5: left_ankle_roll_joint
     *   6: right_hip_pitch_joint,  7: right_hip_roll_joint,  8: right_hip_yaw_joint 9: right_knee_joint 10: right_ankle_pitch_joint 11: right_ankle_roll_joint
     *  12: waist_yaw_joint,       13: waist_roll_joint,     14: waist_pitch_joint,
     *  15: head_pitch_joint,      16: head_yaw_joint
     *  17: left_shoulder_pitch_joint,  18: left_shoulder_roll_joint,  19: left_shoulder_yaw_joint  20: left_elbow_joint
     *  21: left_hand_yaw_joint,  22: left_hand_roll_joint,  23: left_hand_pitch_joint
     *  24: right_shoulder_pitch_joint,  25: right_shoulder_roll_joint,  26: right_shoulder_yaw_joint,  27: right_elbow_joint
     *  28: right_hand_yaw_joint,  29: right_hand_roll_joint,  30: right_hand_pitch_joint
     *
     * @param cmd The RobotCmd object representing the desired robot command.
     * @return True if the command was successfully published, otherwise false.
     */
    bool publishRobotCmd(const RobotCmd &cmd) override;

    /**
     * @brief Method to subscribe to sensor inputs related to a joystick from the robot.
     * @param cb The callback function to be invoked when sensor input from a joystick is received from the robot.
     */
    void subscribeSensorJoy(std::function<void(const SensorJoyConstPtr &)> cb) override;

    /**
     * @brief Method to subscribe to diagnostic values from the robot.
     *
     * Examples:
     * | name        | level  | code | msg
     * |-------------|--------|------|--------------------
     * | imu         | OK     | 0    | - IMU is functioning properly.
     * | imu         | ERROR  | -1   | - Error in IMU.
     * |-------------|--------|------|--------------------
     * | ethercat    | OK     | 0    | - EtherCAT is working fine.
     * | ethercat    | ERROR  | -1   | - EtherCAT error.
     * |-------------|--------|------|--------------------
     * | calibration | OK     | 0    | - Robot calibration successful.
     * | calibration | WARN   | 1    | - Robot calibration in progress.
     * | calibration | ERROR  | -1   | - Robot calibration failed.
     * |-------------|--------|------|--------------------
     *
     * @param cb The callback function to be invoked when diagnostic values are received from the robot.
     */
    void subscribeDiagnosticValue(std::function<void(const DiagnosticValueConstPtr &)> cb) override;

    /**
     * @brief Destructor for the Humanoid class.
     *        Cleans up any resources used by the object.
     */
    virtual ~Humanoid();

  private:
    /**
     * @brief Private constructor to prevent external instantiation of the Humanoid class.
     */
    Humanoid();
  };
}

#endif