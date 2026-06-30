import { PIPELINE_STEPS as ARTICLE_STEPS } from "./pipeline";
import { SOCIAL_PIPELINE_STEPS as SOCIAL_STEPS } from "./socialPipeline";

export const PIPELINE_IDS = {
  ARTICLE: "article",
  SOCIAL: "social_media",
};

export function stepsForPipeline(pipelineId) {
  if (pipelineId === PIPELINE_IDS.SOCIAL) return SOCIAL_STEPS;
  return ARTICLE_STEPS;
}

export function stepKeysForPipeline(pipelineId) {
  return stepsForPipeline(pipelineId).map((s) => s.key);
}

