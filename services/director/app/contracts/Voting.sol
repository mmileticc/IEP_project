// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// @title OrderVoting
/// @notice One-shot majority-vote contract deployed by the director service
/// for a single pending buy/sell order. Only the pre-selected `voters` may
/// vote, each at most once; the order is settled the moment either side
/// reaches a strict majority (n / 2 + 1), after which further votes revert.
contract OrderVoting {
    address[] public voters;
    mapping(address => bool) public isVoter;
    mapping(address => bool) public hasVoted;

    uint256 public immutable majority;
    uint256 public approveCount;
    uint256 public rejectCount;

    bool public finished;
    bool public approved;

    event VoteCast(address indexed voter, bool inFavor);
    event VotingFinished(bool approved);

    constructor(address[] memory _voters) {
        require(_voters.length % 2 == 1, "Even number of voters.");
        voters = _voters;
        for (uint256 i = 0; i < _voters.length; i++) {
            isVoter[_voters[i]] = true;
        }
        majority = _voters.length / 2 + 1;
    }

    function approveOrder() external {
        _vote(true);
    }

    function rejectOrder() external {
        _vote(false);
    }

    function _vote(bool inFavor) internal {
        require(!finished, "Voting ended.");
        require(isVoter[msg.sender], "Invalid address.");
        require(!hasVoted[msg.sender], "Already voted.");

        hasVoted[msg.sender] = true;

        if (inFavor) {
            approveCount += 1;
        } else {
            rejectCount += 1;
        }

        emit VoteCast(msg.sender, inFavor);

        if (approveCount >= majority) {
            finished = true;
            approved = true;
            emit VotingFinished(true);
        } else if (rejectCount >= majority) {
            finished = true;
            approved = false;
            emit VotingFinished(false);
        }
    }
}
