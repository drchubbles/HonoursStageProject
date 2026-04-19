
# This section imports the tools used by the local submission summariser.
from __future__ import annotations

import json
import re
from dataclasses import dataclass


# This function tidies summary text before it is reused by the summariser.
def normalizeSummaryText(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


# This function creates a comparison key from summary text.
def normalizeSummaryKey(value):
    return normalizeSummaryText(value).lower()


# This function shortens summary text to a safe display length.
def truncateSummaryText(value, maxLength):
    valueText = normalizeSummaryText(value)
    if len(valueText) <= maxLength:
        return valueText
    return valueText[: max(0, int(maxLength) - 1)].rstrip() + "…"


# This data class stores the result returned by the local summariser service.
@dataclass
class LocalSubmissionSummaryResult:
    status: str
    summaryText: str = ""
    payloadJson: str = ""
    modelName: str = ""
    message: str = ""


# This factory chooses the summariser service that matches the current config.
class LocalSubmissionSummaryServiceFactory:

    # This method builds the right local summariser service for the current configuration.
    @staticmethod
    def create(config):
        summaryMode = normalizeSummaryKey((config or {}).get("LOCAL_SUMMARY_MODE") or "rule_based")
        if summaryMode in {"off", "disabled", "none"}:
            return DisabledSubmissionSummaryService(config)
        return RuleBasedSubmissionSummaryService(config)


# This service returns a disabled result when local summarising is turned off.
class DisabledSubmissionSummaryService:

    # This method handles init for disabled submission summary service.
    def __init__(self, config):
        self.config = config or {}


    # This method returns a disabled summary result without generating any summary text.
    def generateSummary(self, *, formTitle, submissionId, submittedAt, answerSummary):
        payload = {
            "formTitle": normalizeSummaryText(formTitle),
            "submissionId": submissionId,
            "submittedAt": str(submittedAt) if submittedAt else None,
            "answeredQuestionCount": len([item for item in (answerSummary or []) if normalizeSummaryText((item or {}).get("answerText"))]),
            "summaryMode": "disabled",
        }
        return LocalSubmissionSummaryResult(
            status="disabled",
            summaryText="",
            payloadJson=json.dumps(payload, ensure_ascii=False),
            modelName="disabled",
            message="Local summariser is disabled.",
        )


# This service creates rule-based summaries from saved submission answers.
class RuleBasedSubmissionSummaryService:

    # This method handles init for rule based submission summary service.
    def __init__(self, config):
        self.config = config or {}
        self.modelName = normalizeSummaryText(self.config.get("LOCAL_SUMMARY_MODEL_NAME") or "localRuleBasedSummariser-v3")
        try:
            self.maxDetailChars = int(self.config.get("LOCAL_SUMMARY_MAX_DETAIL_CHARS") or 320)
        except (TypeError, ValueError):
            self.maxDetailChars = 320


    # This method turns saved answers into a rule-based summary and payload record.
    def generateSummary(self, *, formTitle, submissionId, submittedAt, answerSummary):
        answeredItems = []
        for item in answerSummary or []:
            promptText = normalizeSummaryText((item or {}).get("promptText"))
            answerText = normalizeSummaryText((item or {}).get("answerText"))
            if not promptText or not answerText:
                continue
            answeredItems.append({
                "questionVersionId": (item or {}).get("questionVersionId"),
                "promptText": promptText,
                "promptKey": normalizeSummaryKey((item or {}).get("promptKey") or promptText),
                "answerText": answerText,
            })

        targetInfo = self.findTargets(answeredItems)
        issueItems = []
        detailItems = []
        contextItems = []
        neutralItems = []

        for item in answeredItems:
            promptKey = item["promptKey"]
            if self.isIdentityPrompt(promptKey):
                continue
            if self.isDetailPrompt(promptKey):
                detailItems.append(item)
            elif self.answerLooksLikeIssue(promptKey, item["answerText"]):
                issueItems.append(item)
            elif self.isContextPrompt(promptKey):
                contextItems.append(item)
            else:
                neutralItems.append(item)

        summaryText = self.buildSummaryText(
            formTitle=formTitle,
            targetInfo=targetInfo,
            issueItems=issueItems,
            detailItems=detailItems,
            contextItems=contextItems,
            neutralItems=neutralItems,
        )

        payload = {
            "formTitle": normalizeSummaryText(formTitle),
            "submissionId": submissionId,
            "submittedAt": str(submittedAt) if submittedAt else None,
            "subjectName": targetInfo.get("subjectName") or "",
            "subjectEmail": targetInfo.get("subjectEmail") or "",
            "supervisorName": targetInfo.get("supervisorName") or "",
            "supervisorEmail": targetInfo.get("supervisorEmail") or "",
            "logNumber": targetInfo.get("logNumber") or "",
            "team": targetInfo.get("team") or "",
            "issueSignals": [self.buildPairText(item) for item in issueItems[:5]],
            "detailExtracts": [self.buildPairText(item, maxAnswerLength=self.maxDetailChars) for item in detailItems[:3]],
            "context": [self.buildPairText(item, maxAnswerLength=120) for item in contextItems[:4]],
            "answeredQuestionCount": len(answeredItems),
            "summaryMode": "rule_based",
        }

        return LocalSubmissionSummaryResult(
            status="generated",
            summaryText=summaryText,
            payloadJson=json.dumps(payload, ensure_ascii=False),
            modelName=self.modelName,
            message="Local summary generated.",
        )


    # This method handles targets for rule based submission summary service.
    def findTargets(self, answerSummary):
        subjectName = ""
        subjectEmail = ""
        supervisorName = ""
        supervisorEmail = ""
        logNumber = ""
        team = ""
        for item in answerSummary or []:
            promptKey = item.get("promptKey") or ""
            answerText = normalizeSummaryText(item.get("answerText"))
            if not answerText:
                continue
            if ("staff member" in promptKey or "member of staff" in promptKey or "requiring feedback" in promptKey) and "supervisor" not in promptKey and "email" not in promptKey and not subjectName:
                subjectName = answerText
            elif ("staff member" in promptKey or "member of staff" in promptKey or "requiring feedback" in promptKey) and "email" in promptKey and "supervisor" not in promptKey and not subjectEmail:
                subjectEmail = answerText
            elif "supervisor" in promptKey and "email" not in promptKey and not supervisorName:
                supervisorName = answerText
            elif "supervisor" in promptKey and "email" in promptKey and not supervisorEmail:
                supervisorEmail = answerText
            elif "log number" in promptKey and not logNumber:
                logNumber = answerText
            elif "team" in promptKey and not team:
                team = answerText
        return {
            "subjectName": subjectName,
            "subjectEmail": subjectEmail,
            "supervisorName": supervisorName,
            "supervisorEmail": supervisorEmail,
            "logNumber": logNumber,
            "team": team,
        }


    # This method handles identity prompt for rule based submission summary service.
    def isIdentityPrompt(self, promptKey):
        identityKeywords = [
            "email",
            "log number",
            "name",
            "supervisor",
            "team",
            "submitted by",
        ]
        if "staff member" in promptKey or "member of staff" in promptKey:
            return True
        return any(keyword in promptKey for keyword in identityKeywords)


    # This method handles detail prompt for rule based submission summary service.
    def isDetailPrompt(self, promptKey):
        detailKeywords = [
            "comment",
            "details",
            "detail",
            "summary",
            "description",
            "reason",
            "explain",
            "precise",
            "feedback",
            "notes",
            "what happened",
        ]
        return any(keyword in promptKey for keyword in detailKeywords)


    # This method handles context prompt for rule based submission summary service.
    def isContextPrompt(self, promptKey):
        contextKeywords = [
            "opening code",
            "crime",
            "negated",
            "team",
            "log number",
            "outcome",
            "category",
            "priority",
            "severity",
        ]
        return any(keyword in promptKey for keyword in contextKeywords)


    # This method handles issue-signal checks for issue for rule based submission summary service.
    def answerLooksLikeIssue(self, promptKey, answerText):
        answerKey = normalizeSummaryKey(answerText)
        if not answerKey:
            return False

        noIssueValues = {"no", "n", "false", "none", "n/a", "na", "not applicable", "correct", "compliant", "pass", "passed", "good"}
        issueValues = {"yes", "y", "true", "incorrect", "not correct", "failed", "fail", "poor", "missed", "required", "present"}

        if any(keyword in promptKey for keyword in ["correct", "compliant", "accurate", "right"]):
            return answerKey in {"no", "false", "incorrect", "not correct", "failed", "fail", "poor"}

        if any(keyword in promptKey for keyword in ["missed", "not negated", "error", "issue", "problem", "breach", "concern"]):
            if answerKey in noIssueValues:
                return False
            if answerKey in issueValues:
                return True
            return False

        return False


    # This method handles pair text for rule based submission summary service.
    def buildPairText(self, item, maxAnswerLength=90):
        promptText = normalizeSummaryText((item or {}).get("promptText") or "Question")
        answerText = truncateSummaryText((item or {}).get("answerText") or "", maxAnswerLength)
        return f"{promptText}: {answerText}"


    # This method handles trivial detail value for rule based submission summary service.
    def isTrivialDetailValue(self, value):
        answerKey = normalizeSummaryKey(value)
        if not answerKey:
            return True
        trivialValues = {
            "hi",
            "hello",
            "test",
            "n/a",
            "na",
            "none",
            "no",
            "nothing",
            "no detail",
            "no details",
            "no additional detail",
            "no additional details",
            "no further detail",
            "no further details",
            "nil",
            "ok",
            "okay",
            "cool",
            "fine",
            "good",
            "all good",
            "looks good",
        }
        if answerKey in trivialValues:
            return True
        if re.fullmatch(r"example\s*\d+", answerKey):
            return True
        if all(re.fullmatch(r"example\s*\d+", part.strip()) for part in answerKey.split(",") if part.strip()):
            return True
        if len(answerKey) <= 3 and answerKey not in {"mx1", "mx2", "ddm"}:
            return True
        return False


    # This method handles meaningful team value for rule based submission summary service.
    def isMeaningfulTeamValue(self, value):
        answerKey = normalizeSummaryKey(value)
        if not answerKey:
            return False
        if re.fullmatch(r"example\s*\d+", answerKey):
            return False
        return True


    # This method handles subject label for rule based submission summary service.
    def buildSubjectLabel(self, targetInfo):
        subjectName = normalizeSummaryText(targetInfo.get("subjectName"))
        return subjectName or "the named staff member"


    # This method handles context sentence for rule based submission summary service.
    def buildContextSentence(self, contextItems):
        if not contextItems:
            return ""
        noIssuePairs = []
        generalPairs = []
        for item in contextItems:
            if self.isTrivialDetailValue(item.get("answerText")):
                continue
            pairText = self.buildPairText(item, maxAnswerLength=60)
            if not self.answerLooksLikeIssue(item.get("promptKey") or "", item.get("answerText") or ""):
                noIssuePairs.append(pairText)
            else:
                generalPairs.append(pairText)
        if noIssuePairs and not generalPairs:
            return f"No issue flags were recorded in the fixed-choice answers: {'; '.join(noIssuePairs[:3])}."
        if generalPairs:
            return f"Recorded context includes {'; '.join((generalPairs + noIssuePairs)[:3])}."
        if noIssuePairs:
            return f"Recorded context includes {'; '.join(noIssuePairs[:3])}."
        return ""


    # This method handles supervisor sentence for rule based submission summary service.
    def buildSupervisorSentence(self, targetInfo):
        supervisorName = normalizeSummaryText(targetInfo.get("supervisorName"))
        supervisorEmail = normalizeSummaryText(targetInfo.get("supervisorEmail"))
        if supervisorName:
            return f"Supervisor recorded for follow-up: {supervisorName}."
        if supervisorEmail:
            return f"Supervisor email recorded for follow-up: {supervisorEmail}."
        return ""


    # This method handles issue sentence for rule based submission summary service.
    def buildIssueSentence(self, issueItems):
        issueFragments = []
        for item in issueItems[:3]:
            promptKey = item.get("promptKey") or ""
            answerKey = normalizeSummaryKey(item.get("answerText") or "")
            if "opening code" in promptKey and any(keyword in promptKey for keyword in ["correct", "accurate", "right"]):
                if answerKey in {"no", "false", "incorrect", "not correct", "failed", "fail", "poor"}:
                    issueFragments.append("the opening code was marked as incorrect")
                    continue
            if "crime" in promptKey and ("missed" in promptKey or "negated" in promptKey):
                if answerKey in {"yes", "y", "true", "present", "required", "missed"}:
                    issueFragments.append("crime(s) were marked as missed or not negated")
                    continue
            issueFragments.append(self.buildPairText(item, maxAnswerLength=60))
        if not issueFragments:
            return ""
        if len(issueFragments) == 1:
            return f"A potential issue was recorded: {issueFragments[0]}."
        return f"Potential issues recorded were {'; '.join(issueFragments)}."


    # This method handles prompt matches issue area for rule based submission summary service.
    def promptMatchesIssueArea(self, item, issueItems):
        promptKey = normalizeSummaryKey((item or {}).get("promptKey") or (item or {}).get("promptText") or "")
        if not promptKey:
            return False
        if "crime" in promptKey and ("missed" in promptKey or "negated" in promptKey):
            return any("crime" in (issueItem.get("promptKey") or "") and ("missed" in (issueItem.get("promptKey") or "") or "negated" in (issueItem.get("promptKey") or "")) for issueItem in issueItems)
        if "opening code" in promptKey:
            return any("opening code" in (issueItem.get("promptKey") or "") for issueItem in issueItems)
        return False


    # This method handles supporting detail item for rule based submission summary service.
    def findSupportingDetailItem(self, issueItems, detailItems, contextItems):
        candidateGroups = [contextItems, detailItems]
        for candidateGroup in candidateGroups:
            for item in candidateGroup:
                answerText = item.get("answerText") or ""
                if self.isTrivialDetailValue(answerText):
                    continue
                if self.promptMatchesIssueArea(item, issueItems):
                    return item
        for candidateGroup in candidateGroups:
            for item in candidateGroup:
                answerText = item.get("answerText") or ""
                if self.isTrivialDetailValue(answerText):
                    continue
                return item
        return None


    # This method handles summary text for rule based submission summary service.
    def buildSummaryText(self, *, formTitle, targetInfo, issueItems, detailItems, contextItems, neutralItems):
        cleanFormTitle = normalizeSummaryText(formTitle) or "form"
        sentenceParts = [f"This {cleanFormTitle} submission relates to {self.buildSubjectLabel(targetInfo)}."]

        if issueItems:
            issueSentence = self.buildIssueSentence(issueItems)
            if issueSentence:
                sentenceParts.append(issueSentence)
        else:
            contextSentence = self.buildContextSentence(contextItems)
            if contextSentence:
                sentenceParts.append(contextSentence)
            elif neutralItems:
                filteredNeutralItems = [item for item in neutralItems if not self.isTrivialDetailValue(item.get("answerText"))]
                if filteredNeutralItems:
                    neutralText = "; ".join(self.buildPairText(item, maxAnswerLength=60) for item in filteredNeutralItems[:2])
                    sentenceParts.append(f"The submission mainly records {neutralText}.")
                else:
                    sentenceParts.append("The local summariser recorded the answered items without detecting a clear issue flag.")
            else:
                sentenceParts.append("The local summariser recorded the answered items without detecting a clear issue flag.")

        supportingDetailItem = self.findSupportingDetailItem(issueItems, detailItems, contextItems)
        if supportingDetailItem:
            detailText = truncateSummaryText(supportingDetailItem.get("answerText") or "", self.maxDetailChars).rstrip(".!?")
            sentenceParts.append(f"Supporting detail recorded: {detailText}.")

        supervisorSentence = self.buildSupervisorSentence(targetInfo)
        if supervisorSentence:
            sentenceParts.append(supervisorSentence)

        return " ".join(part for part in sentenceParts if normalizeSummaryText(part))
