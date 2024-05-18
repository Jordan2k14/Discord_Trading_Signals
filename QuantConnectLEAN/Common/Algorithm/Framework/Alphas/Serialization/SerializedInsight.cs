/*
 * QUANTCONNECT.COM - Democratizing Finance, Empowering Individuals.
 * Lean Algorithmic Trading Engine v2.0. Copyright 2014 QuantConnect Corporation.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
*/

using Newtonsoft.Json;
using QuantConnect.Util;
using System;

namespace QuantConnect.Algorithm.Framework.Alphas.Serialization
{
    /// <summary>
    /// DTO used for serializing an insight that was just generated by an algorithm.
    /// This type does not contain any of the analysis dependent fields, such as scores
    /// and estimated value
    /// </summary>
    public class SerializedInsight
    {
        private double _createdTime;

        /// <summary>
        /// See <see cref="Insight.Id"/>
        /// </summary>
        public string Id { get; set; }

        /// <summary>
        /// See <see cref="Insight.GroupId"/>
        /// </summary>
        public string GroupId { get; set; }

        /// <summary>
        /// See <see cref="Insight.SourceModel"/>
        /// </summary>
        public string SourceModel { get; set; }

        /// <summary>
        /// Pass-through for <see cref="CreatedTime"/>
        /// </summary>
        [Obsolete("Deprecated as of 2020-01-23. Please use the `CreatedTime` property instead.")]
        public double GeneratedTime
        {
            get { return _createdTime; }
            set { _createdTime = value; }
        }

        /// <summary>
        /// See <see cref="Insight.GeneratedTimeUtc"/>
        /// </summary>
        public double CreatedTime
        {
            get { return _createdTime; }
            set { _createdTime = value; }
        }

        /// <summary>
        /// See <see cref="Insight.CloseTimeUtc"/>
        /// </summary>
        public double CloseTime { get; set; }

        /// <summary>
        /// See <see cref="Insight.Symbol"/>
        /// The symbol's security identifier string
        /// </summary>
        public string Symbol { get; set; }

        /// <summary>
        /// See <see cref="Insight.Symbol"/>
        /// The symbol's ticker at the generated time
        /// </summary>
        public string Ticker { get; set; }

        /// <summary>
        /// See <see cref="Insight.Type"/>
        /// </summary>
        public InsightType Type { get; set; }

        /// <summary>
        /// See <see cref="Insight.ReferenceValue"/>
        /// </summary>
        [JsonProperty("reference")]
        public decimal ReferenceValue { get; set; }

        /// <summary>
        /// See <see cref="Insight.ReferenceValueFinal"/>
        /// </summary>
        public decimal ReferenceValueFinal { get; set; }

        /// <summary>
        /// See <see cref="Insight.Direction"/>
        /// </summary>
        public InsightDirection Direction { get; set; }

        /// <summary>
        /// See <see cref="Insight.Period"/>
        /// </summary>
        public double Period { get; set; }

        /// <summary>
        /// See <see cref="Insight.Magnitude"/>
        /// </summary>
        [JsonConverter(typeof(JsonRoundingConverter))]
        public double? Magnitude { get; set; }

        /// <summary>
        /// See <see cref="Insight.Confidence"/>
        /// </summary>
        [JsonConverter(typeof(JsonRoundingConverter))]
        public double? Confidence { get; set; }

        /// <summary>
        /// See <see cref="Insight.Weight"/>
        /// </summary>
        public double? Weight { get; set; }

        /// <summary>
        /// See <see cref="InsightScore.IsFinalScore"/>
        /// </summary>
        public bool ScoreIsFinal { get; set; }

        /// <summary>
        /// See <see cref="InsightScore.Magnitude"/>
        /// </summary>
        [JsonConverter(typeof(JsonRoundingConverter))]
        public double ScoreMagnitude { get; set; }

        /// <summary>
        /// See <see cref="InsightScore.Direction"/>
        /// </summary>
        [JsonConverter(typeof(JsonRoundingConverter))]
        public double ScoreDirection { get; set; }

        /// <summary>
        /// See <see cref="Insight.EstimatedValue"/>
        /// </summary>
        [JsonConverter(typeof(JsonRoundingConverter))]
        public decimal EstimatedValue { get; set; }

        /// <summary>
        /// See <see cref="Insight.Tag"/>
        /// </summary>
        public string Tag { get; set; }

        /// <summary>
        /// Initializes a new default instance of the <see cref="SerializedInsight"/> class
        /// </summary>
        public SerializedInsight()
        {
        }

        /// <summary>
        /// Initializes a new instance of the <see cref="SerializedInsight "/> class by copying the specified insight
        /// </summary>
        /// <param name="insight">The insight to copy</param>
        public SerializedInsight(Insight insight)
        {
            Id = insight.Id.ToStringInvariant("N");
            SourceModel = insight.SourceModel;
            GroupId = insight.GroupId?.ToStringInvariant("N");
            CreatedTime = Time.DateTimeToUnixTimeStamp(insight.GeneratedTimeUtc);
            CloseTime = Time.DateTimeToUnixTimeStamp(insight.CloseTimeUtc);
            Symbol = insight.Symbol.ID.ToString();
            Ticker = insight.Symbol.Value;
            Type = insight.Type;
            ReferenceValue = insight.ReferenceValue;
            ReferenceValueFinal = insight.ReferenceValueFinal;
            Direction = insight.Direction;
            Period = insight.Period.TotalSeconds;
            Magnitude = insight.Magnitude;
            Confidence = insight.Confidence;
            ScoreIsFinal = insight.Score.IsFinalScore;
            ScoreMagnitude = insight.Score.Magnitude;
            ScoreDirection = insight.Score.Direction;
            EstimatedValue = insight.EstimatedValue;
            Weight = insight.Weight;
            Tag = insight.Tag;
        }

        #region BackwardsCompatibility
        [JsonProperty("group-id")]
        string OldGroupId
        {
            set
            {
                GroupId = value;
            }
        }

        [JsonProperty("source-model")]
        string OldSourceModel
        {
            set
            {
                SourceModel = value;
            }
        }

        [JsonProperty("generated-time")]
        double OldGeneratedTime
        {
            set
            {
                GeneratedTime = value;
            }
        }

        [JsonProperty("created-time")]
        public double OldCreatedTime
        {
            set
            {
                CreatedTime = value;
            }
        }

        [JsonProperty("close-time")]
        public double OldCloseTime
        {
            set
            {
                CloseTime = value;
            }
        }

        [JsonProperty("reference-final")]
        decimal OldReferenceValueFinal
        {
            set
            {
                ReferenceValueFinal = value;
            }
        }

        [JsonProperty("score-final")]
        bool OldScoreIsFinal
        {
            set
            {
                ScoreIsFinal = value;
            }
        }

        [JsonProperty("score-magnitude")]
        [JsonConverter(typeof(JsonRoundingConverter))]
        double OldScoreMagnitude
        {
            set
            {
                ScoreMagnitude = value;
            }
        }

        [JsonProperty("score-direction")]
        [JsonConverter(typeof(JsonRoundingConverter))]
        double OldScoreDirection
        {
            set
            {
                ScoreDirection = value;
            }
        }

        [JsonProperty("estimated-value")]
        [JsonConverter(typeof(JsonRoundingConverter))]
        decimal OldEstimatedValue
        {
            set
            {
                EstimatedValue = value;
            }
        }
        #endregion
    }
}